"""Runtime patches for the openai SDK.

Idempotent. Installed once on first SDK use via the lazy-loader paths in
``run_agent.py`` and ``agent/auxiliary_client.py``.
"""

_installed = False


def install_response_output_none_guard() -> None:
    """Guard ``parse_response`` against ``response.output is None``.

    The chatgpt.com/backend-api/codex streaming protocol terminates with an
    event whose ``response.output`` is ``None`` (not ``[]``). The SDK's
    ``parse_response`` iterates that field unconditionally::

        for output in response.output:
            ...

    so the very first primary call crashes with
    ``TypeError: 'NoneType' object is not iterable`` and the agent falls
    over to MiniMax on every turn. Both openai 2.24 and 2.36 carry the same
    unguarded iteration; the bug is upstream and not version-specific.
    Coerce ``None -> []`` so the parser produces an empty
    ``ParsedResponse`` and Hermes' existing backfill paths
    (``run_agent.py`` near ``final_response.output = list(...)``) recover
    the actual content from the streamed deltas.
    """
    global _installed
    if _installed:
        return

    from openai.lib._parsing import _responses as _parsing_responses
    from openai.lib.streaming.responses import _responses as _streaming_responses

    _orig = _parsing_responses.parse_response

    def _guarded(*, text_format, input_tools, response):
        if getattr(response, "output", None) is None:
            try:
                response.output = []
            except Exception:
                pass
        return _orig(
            text_format=text_format,
            input_tools=input_tools,
            response=response,
        )

    _parsing_responses.parse_response = _guarded
    _streaming_responses.parse_response = _guarded
    _installed = True
