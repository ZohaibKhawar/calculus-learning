"""One place to reach Claude for the study helper chat and the forum check.

Optional. Both switch on when ANTHROPIC_API_KEY is set (in the environment or in
secrets.env) and the `anthropic` package is installed. Without them the chat answers
from the site's own lessons and the forum check uses built-in rules.
"""
import settings

# Anthropic's lowest-cost model. A bigger one ("claude-sonnet-5-5", "claude-opus-5-5") is
# better at math and costs more for every message.
MODEL = "claude-haiku-4-5"

_client = None


class Unavailable(Exception):
    """The AI couldn't answer this time (an API error, a refusal): use the built-in rules."""


def available():
    if not settings.ANTHROPIC_API_KEY:
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def client():
    global _client
    if _client is None:
        import anthropic
        # Ask for gzip only. Left alone, the HTTP library also offers Brotli whenever a
        # `brotli` package is installed, and then can't read the answer if that package is
        # an old one (as on PythonAnywhere): every request fails with a connection error.
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY,
                                      default_headers={"Accept-Encoding": "gzip"})
    return _client


def ask(system, messages, max_tokens, timeout, schema=None):
    """One short request to Claude. Returns its text, or raises Unavailable.

    A visitor is waiting on the answer, so the request gives up after `timeout`
    seconds instead of retrying.
    """
    import anthropic
    # With a schema, the answer comes back as JSON in exactly that shape.
    shape = {"output_config": {"format": {"type": "json_schema", "schema": schema}}} if schema else {}
    try:
        msg = client().with_options(timeout=timeout, max_retries=0).messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            **shape,
        )
    except anthropic.APIError as e:
        raise Unavailable(type(e).__name__)
    if msg.stop_reason == "refusal":
        raise Unavailable("refusal")
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if not text:
        raise Unavailable("empty")
    return text
