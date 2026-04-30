# Switching from OpenRouter routing to a direct LLM provider

A guide based on the Hermes-side migration from OpenRouter routing
(slug `minimax/minimax-m2.7`) to direct MiniMax via subscription
(slug `MiniMax-M2.7`). The pattern translates to any direct provider
switch (Anthropic, MiniMax, MoonShot/Kimi, GLM, etc.).

## Mental model

Hermes routes LLM calls based on **the model slug format** when
`model.provider = auto`:

| Slug format | Where Hermes looks | Auth env var |
|---|---|---|
| `provider/model` (e.g. `minimax/minimax-m2.7`) | OpenRouter catalog | `OPENROUTER_API_KEY` |
| Plain model name (e.g. `MiniMax-M2.7`) | Direct provider catalog matching the model | `<PROVIDER>_API_KEY` |

The slash IS the routing decision. Mixed-case slugs like
`minimax/MiniMax-M2.7` are **wrong** — they look like OpenRouter slugs
syntactically, route through OpenRouter, but use a direct-provider
model name OpenRouter doesn't recognize → 401 / "User not found".

## What needs to be aligned

Five things must match for direct-provider routing to work:

1. **`MINIMAX_API_KEY` env var** in Railway — the actual API key
2. **`model.default`** in `config.yaml` → `MiniMax-M2.7` (no slash)
3. **`model.provider`** in `config.yaml` → `minimax` (or `auto` if
   alone in credential pool — but explicit is safer)
4. **`model.base_url`** in `config.yaml` → `https://api.minimax.io/anthropic`
   (or unset to inherit from provider config — but Hermes sometimes
   leaves stale OpenRouter base_url after switching, so set it
   explicitly)
5. **`auth.json` `credential_pool`** must have a `minimax` entry, AND
   `active_provider` at the top level must be set to `minimax`

## Pitfalls we hit

### 1. The fork picks up new env vars only on first boot

Hermes generates `auth.json` from env vars on first boot. Adding
`MINIMAX_API_KEY` *after* `auth.json` already exists doesn't
auto-register the new provider — only OpenRouter ends up in the
credential pool.

**Fix:** explicitly add the credential. Either via CLI:
```bash
hermes auth add minimax --type api-key --api-key "$MINIMAX_API_KEY"
```
…or directly edit `auth.json` (we shipped `scripts/add_minimax_auth.py`
for this on the Hermes side — adapt the same approach for GordonClaw).

### 2. With multiple credentials in the pool, `active_provider` controls routing

If the credential pool has both `openrouter` and `minimax` but
`active_provider` is unset, Hermes falls back to whatever's first —
which gave us OpenRouter → 401 with the disabled key.

**Fix:** set `active_provider = minimax` at the top level of
`auth.json`. We shipped `scripts/set_active_provider.py` for this.

### 3. `model.base_url` drift between provider switches

When you change `model.provider`, Hermes does *not* reset
`model.base_url`. We set `model.provider = minimax` but
`model.base_url` was still `https://openrouter.ai/api/v1` — so
requests went to OpenRouter's URL with the MiniMax key → 401.

**Fix:** explicitly set `model.base_url` to match the provider, or
clear it.

### 4. Auxiliary tasks have their own config

Title generation, compression summarization, and similar internal
tasks use a **separate** auxiliary LLM client with its own
`auxiliary.<task>.{provider,model,base_url}` config. Switching
`model.default` doesn't switch them. We saw `HTTP 404 page not found`
from title generation because it was hitting a stale base URL.

**Fix:** set `auxiliary.title_generation.{provider,model}` (and
similarly for `compression` if it's failing) to match the main provider.

### 5. The bundled `cli-config.yaml.example` default is dangerous

If `config.yaml` ever gets re-seeded (volume reset, profile clone),
Hermes copies from the bundled example which sets
`model.default = anthropic/claude-opus-4.6`. We burned ~$16 of Opus
tokens overnight before catching this.

**Fix:** enforce critical config keys via the entrypoint on every
boot, env-overridable. See the `# Enforce critical config on every
boot` block in `docker/entrypoint.sh` — re-applies `model.default`,
`model.provider`, `compression.threshold`, and the auxiliary
title-generation config every time, idempotently.

## Verification checklist

After switching providers, run these to confirm correct routing:

```bash
# 1. Test the key + endpoint directly (sanity check)
python3 /opt/hermes/scripts/test_minimax.py
# should print: HTTP 200 + valid response

# 2. Check the credential pool
python3 /opt/hermes/scripts/audit_auth.py
# should show: minimax provider with status=OK and active_provider=minimax

# 3. Check config.yaml
hermes config show | grep -A 1 "Model"
# should show: default='MiniMax-M2.7', provider='minimax',
#              base_url='https://api.minimax.io/anthropic'

# 4. Send a real message
# Telegram: send "hello" → should get a normal response, no 401
```

## Hermes commits for reference

In `rousegordon-ops/hermes-agent`:

- `scripts/add_minimax_auth.py` — direct auth.json fixer
- `scripts/set_active_provider.py` — set top-level active_provider
- `scripts/test_minimax.py` — endpoint sanity check
- `scripts/audit_auth.py` — redacted credential pool dump
- `b607912b` — entrypoint enforcement of title-generation config

## Adapting for GordonClaw

GordonClaw is OpenClaw-based (TypeScript), so the config file is
`/data/openclaw.json` (not YAML), and the provider abstraction is
different. But the same five-things-must-align principle applies.
The reconciler block in `scripts/railway-entrypoint.sh` is the right
place to enforce equivalent settings on every boot — see the
patterns already there for `model.primary` / `fallbacks` / etc.

Cross-reference both ports with this doc when something doesn't work
the first time. The pitfalls above are the ones that took the most
time to diagnose.
