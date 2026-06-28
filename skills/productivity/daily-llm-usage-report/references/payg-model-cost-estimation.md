# Pay-as-you-go model cost estimation

Use this when Gordon asks what it would cost to run Hermes on a metered provider/model instead of an OAuth/subscription provider.

## Data sources

- Request counts: `/opt/data/request-log.jsonl`
  - Each row has `ts`, `api_calls`, `platform`, `duration`, and `model`.
  - Use this for API-call volume and 7d/30d run rates.
- Session transcripts: `/opt/data/sessions/*.jsonl`
  - Current sessions do not reliably store provider usage objects (`prompt_tokens`, `completion_tokens`, etc.).
  - You can approximate assistant output by summing assistant `content`, `reasoning`, `reasoning_content`, and `tool_calls` JSON characters, then dividing by ~4 chars/token.
- Tool schema overhead: read the latest session_meta row and measure `tools` JSON size. This approximates the repeated tool definition payload; divide chars by ~4 for rough tokens.

## Formula

For a candidate model with prices per 1M tokens:

```text
monthly_api_calls = observed_api_calls * 30 / observed_days
monthly_input_tokens = monthly_api_calls * assumed_input_tokens_per_call
monthly_output_tokens = estimated_output_tokens_per_month
cost = (monthly_input_tokens / 1e6 * input_price) + (monthly_output_tokens / 1e6 * output_price)
```

Use ranges rather than a false-precision point estimate. For Hermes gateway with many tools enabled, reasonable first-pass assumptions are 40k/60k/80k input tokens per API call unless actual token telemetry is available.

## GLM 5.2 via OpenRouter snapshot from 2026-06-28

OpenRouter model page for `z-ai/glm-5.2` showed:

- Input: `$0.95 / 1M tokens`
- Output: `$3.00 / 1M tokens`
- Context: `1M`

In Gordon's request log at that point:

- Last 7 days: 505 model API calls → ~2,164/month run-rate.
- Last 30 days: 3,699 model API calls.
- Approx stored assistant output: ~1.1M tokens/month.

Cost range using 40k/60k/80k input tokens per API call:

- 7-day run-rate: about `$85–$170/month` including ~1.1M output tokens.
- 30-day actual run-rate: about `$145–$285/month` including ~1.1M output tokens.
- Practical planning estimate: about `$200/month`.

## Caveats to state

- This is a rough estimate unless the provider returns real token usage and Hermes logs it.
- OpenRouter prompt caching/effective pricing may reduce the real bill if the repeated Hermes system/tool prefix is cached.
- OAuth/subscription-backed providers can have near-zero marginal token cost from Gordon's perspective; metered OpenRouter usage is direct pay-as-you-go spend.
