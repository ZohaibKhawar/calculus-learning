"""Turn an uploaded PDF into a CalcLearners visual lesson with Claude.

Optional feature. It only runs when the `anthropic` package is installed and
credentials are available: an ANTHROPIC_API_KEY environment variable, or a
profile from `ant auth login`. Without them, uploads still get a study plan.

The output uses the same video format as the hand-written lessons in videos/.
"""
import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MODEL = "claude-opus-5-5"


class GenerationError(Exception):
    pass


def available():
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or (Path.home() / ".config" / "anthropic").exists())


SYSTEM = r"""You turn calculus course notes into short, punchy animated video lessons for students who are used to TikTok: fast, visual, friendly, zero filler. Stay faithful to the notes: use their examples, notation and homework problems, and keep every piece of math correct.

VIDEO FORMAT
An episode is a list of scenes. Each scene has a "type" and a list of "beats". A beat is one or two short spoken sentences ("say") plus an optional animation action ("do"). The narration is read aloud by text-to-speech and shown as captions, so "say" must be plain spoken English: write "d y d x", "x squared", "one half", never LaTeX or symbols.

Scene types and their fields:
- title: emoji, text (big headline, under 6 words), sub (subtitle). Two beats work well.
- equation: lines = list of LaTeX lines (no $ delimiters). Each beat reveals the next line ("do": "next", the default) or keeps the screen as is ("do": "hold").
- layers: an onion view of a composite function. layers = list from OUTSIDE to INSIDE, each {label, expr (LaTeX, use \square for the hole), deriv (LaTeX derivative of that layer)}; result = LaTeX final answer. Actions in order: "build", then one "peel" per layer, then "result". Extra beats can "hold".
- graph: curves = list of {fn: expression in x} or {implicit: expression in x and y that equals 0 on the curve}, plus optional label. view = {xmin, xmax, ymin, ymax, equal}; set equal true for circles and implicit curves so shapes are not stretched. Actions (combine with ";"): "draw", "trace" (a dot slides along curve 0 showing the live slope), "tangent:a" (tangent to curve 0 at x=a), "tangentxy:x,y,m" (line through (x,y) with slope m, for implicit curves), "point:x,y", "vline:a" (vertical line test), "hold". Expressions use + - * / ^, parentheses, x, y, pi, e and sin cos tan sec exp ln log sqrt abs, e.g. "cos((exp(2*x)+1)^3)^2" or "x^2*y + x*y^2 + x^3 - 3".
- cards: items = list of {icon (one emoji), title, text}. Each beat reveals the next card.
- compare: left and right = {title, lines (LaTeX)}. Actions in order: "left", "right", "link" (shows they are equivalent), "hold".
- pause: question and answer in LaTeX, seconds (countdown, 4 to 6). Beat 1 asks the viewer to pause and try; beat 2 explains the answer.

Text fields that mix words and math (card text, question text, choices, hints, steps, explanations) use \( ... \) for inline math. LaTeX fields can use \hl{...} (cyan), \pk{...} (pink), \yl{...} (yellow) and \gr{...} (green) to highlight the part being discussed.

STYLE
- Hook in the first beat, e.g. "POV: ..." or a surprising question.
- One idea per beat. Short sentences. Encourage the viewer.
- Mix scene types: every episode should use equation, at least one layers, graph or compare scene, a pause scene, and end with a cards recap.
- An episode covers ONE subtopic and runs 3 to 5 minutes, which is about 450 to 700 spoken words across 25 to 45 beats.

ARTICLE (the reading version of the episode, for students who learn best from text)
"article" is a complete written lesson covering the same content as the episode, about 400 to 800 words, using proper math notation (unlike the narration). Markup:
- "## Heading" for sections, a blank line between paragraphs, "- " bullets, "1. " numbered lists, **bold**, and "> " for a tip or common-mistake callout.
- \( ... \) for inline math and \[ ... \] on its own line for display math.
- Worked examples, one numbered line per step and a final answer:
  ::: example Example title
  1. First step
  2. Second step
  Answer: the final answer
  :::
- A still picture of one of this episode's scenes (N is its 0-based position in "scenes"; use it for graph and layers scenes):
  ::: figure N
  Caption
  :::
- A try-it question whose answer stays hidden until clicked:
  ::: try The question
  The answer and a one-line explanation
  :::
End with a "## Key takeaways" bullet list.

QUESTIONS (after each episode)
- easy: exactly 5 multiple choice. Direct application of the episode's main idea.
- intermediate: exactly 5 multiple choice. Two steps or a small twist.
- advanced: exactly 5 multiple choice. Combine rules, evaluate at a point, or use given values.
- expert: exactly 3 open problems that need real thinking and applying the laws in a new way. Give a hint, the full worked solution as steps, and the final answer.
Multiple choice: 4 choices, "answer" is the 0-based index of the correct one, wrong choices are realistic mistakes, "why" explains in one or two sentences. Vary where the correct answer appears.
Double check every derivative, number and answer index."""

OUTLINE_PROMPT = """Read these notes and plan a video series. Split the material into 3 to 8 episodes, one subtopic each, in the order the notes teach them. For each episode give a title and say exactly which parts of the notes it covers (examples, proofs, homework problems)."""

EPISODE_PROMPT = """Here is the plan for the whole series:
{outline}

Write episode {n} of {total}: "{title}".
It covers: {covers}

Use the notes' own examples and notation for this part. Return the complete episode: title, a one-line hook, the scenes, the article (the reading version), and the questions (5 easy, 5 intermediate, 5 advanced, 3 expert)."""


def _obj(props, required):
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


STR = {"type": "string"}
STRS = {"type": "array", "items": STR}
NUM = {"type": "number"}

OUTLINE_SCHEMA = _obj({
    "title": STR,
    "source": STR,
    "episodes": {"type": "array", "items": _obj({"title": STR, "covers": STR}, ["title", "covers"])},
}, ["title", "source", "episodes"])

SCENE_SCHEMA = _obj({
    "type": {"type": "string", "enum": ["title", "equation", "layers", "graph", "cards", "compare", "pause"]},
    "heading": STR,
    "beats": {"type": "array", "items": _obj({"say": STR, "do": STR}, ["say"])},
    "emoji": STR, "text": STR, "sub": STR,
    "lines": STRS,
    "layers": {"type": "array", "items": _obj({"label": STR, "expr": STR, "deriv": STR}, ["label", "expr", "deriv"])},
    "result": STR,
    "curves": {"type": "array", "items": _obj({"fn": STR, "implicit": STR, "label": STR}, [])},
    "view": _obj({"xmin": NUM, "xmax": NUM, "ymin": NUM, "ymax": NUM, "equal": {"type": "boolean"}},
                 ["xmin", "xmax", "ymin", "ymax"]),
    "items": {"type": "array", "items": _obj({"icon": STR, "title": STR, "text": STR}, ["icon", "title", "text"])},
    "left": _obj({"title": STR, "lines": STRS}, ["title", "lines"]),
    "right": _obj({"title": STR, "lines": STRS}, ["title", "lines"]),
    "question": STR, "answer": STR, "seconds": {"type": "integer"},
}, ["type", "beats"])

MC_SCHEMA = _obj({"q": STR, "choices": STRS, "answer": {"type": "integer"}, "why": STR},
                 ["q", "choices", "answer", "why"])
EXPERT_SCHEMA = _obj({"q": STR, "hint": STR, "steps": STRS, "answer": STR}, ["q", "hint", "steps", "answer"])

EPISODE_SCHEMA = _obj({
    "title": STR,
    "hook": STR,
    "scenes": {"type": "array", "items": SCENE_SCHEMA},
    "article": STR,
    "questions": _obj({
        "easy": {"type": "array", "items": MC_SCHEMA},
        "intermediate": {"type": "array", "items": MC_SCHEMA},
        "advanced": {"type": "array", "items": MC_SCHEMA},
        "expert": {"type": "array", "items": EXPERT_SCHEMA},
    }, ["easy", "intermediate", "advanced", "expert"]),
}, ["title", "hook", "scenes", "article", "questions"])


def _ask(client, content, schema):
    import anthropic
    try:
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            system=SYSTEM,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise GenerationError("The Anthropic API key was rejected. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise GenerationError("Hit the Anthropic rate limit. Wait a minute and press Retry.")
    except anthropic.APIStatusError as e:
        raise GenerationError(f"The AI service returned an error ({e.status_code}). Press Retry to try again.")
    except anthropic.APIConnectionError:
        raise GenerationError("Couldn't reach the AI service. Check your internet connection and press Retry.")

    if msg.stop_reason == "refusal":
        raise GenerationError("The AI declined to turn this file into a lesson.")
    if msg.stop_reason == "max_tokens":
        raise GenerationError("The lesson came out too long. Try a shorter PDF.")
    text = next((b.text for b in msg.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise GenerationError("The AI returned a lesson in the wrong format. Press Retry.")


def generate(pdf_path, progress):
    """Build a whole video lesson from a PDF. Calls progress(message) as it goes."""
    import anthropic
    client = anthropic.Anthropic()
    data = base64.standard_b64encode(Path(pdf_path).read_bytes()).decode()
    # The PDF is cached after the first call, so each episode call re-reads it cheaply.
    doc = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data},
           "cache_control": {"type": "ephemeral"}}

    progress("Reading your PDF and planning the episodes…")
    outline = _ask(client, [doc, {"type": "text", "text": OUTLINE_PROMPT}], OUTLINE_SCHEMA)
    plan = outline.get("episodes", [])[:8]
    if not plan:
        raise GenerationError("Couldn't find any calculus topics in this PDF.")

    outline_text = "\n".join(f"{i + 1}. {e['title']}: {e['covers']}" for i, e in enumerate(plan))
    episodes = [None] * len(plan)
    progress(f"Writing {len(plan)} episodes… 0 of {len(plan)} done")
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(_ask, client, [doc, {"type": "text", "text": EPISODE_PROMPT.format(
            outline=outline_text, n=i + 1, total=len(plan), title=e["title"], covers=e["covers"])}],
            EPISODE_SCHEMA): i for i, e in enumerate(plan)}
        for done, job in enumerate(as_completed(jobs), 1):
            episodes[jobs[job]] = job.result()
            progress(f"Writing {len(plan)} episodes… {done} of {len(plan)} done")

    return {"title": outline.get("title") or "Your lesson", "source": outline.get("source", ""), "episodes": episodes}
