# OpenAI Subscription Bridge Provider

## Position

The OpenAI subscription bridge is allowed as an optional single-tenant LLM provider when the DVR agent is used by one customer/operator who intentionally relies on their OpenAI subscription/session instead of server-side API billing.

It should be implemented behind the same provider interface as official API providers, so the system can switch or fall back.

## Provider Interface

```python
class LlmProvider(Protocol):
    name: str
    mode: Literal["api", "subscription_bridge", "mock"]

    async def generate(self, request: LlmRequest) -> LlmResponse:
        ...

    async def health(self) -> ProviderHealth:
        ...
```

Supported providers:

- `openai_api`: official API key, best for stable production/server workloads.
- `openai_subscription_bridge`: single-tenant customer subscription/session, useful when the customer owns the interaction and accepts session dependency.
- `local_mock`: deterministic testing without LLM calls.

## Guardrails

- Use only for one customer/tenant per bridge session.
- Never pool multiple customers through one subscription session.
- Do not hide provider identity. Store provider name/mode in every DVR run.
- Treat session expiry as normal: fail gracefully, ask reconnect, or switch provider if configured.
- Do not store subscription cookies/tokens in prompts, logs, learning memory, or wiki.
- Do not expose bridge controls to regular client commands.
- Add a health check before long DVR generation.
- Keep provider fallback explicit, not silent.

## Traceability

Every generated artifact should record:

```json
{
  "llm_provider": "openai_subscription_bridge",
  "provider_session_id": "redacted_or_hash",
  "model_label": "provider_reported_model",
  "generated_at": "2026-05-27T18:00:00Z",
  "prompt_versions": {},
  "rag_policy_version": "v1"
}
```

Do not store raw credentials or session cookies.

## When To Prefer API Key

Prefer official API/server-side provider when:

- multiple customers use the system;
- SLA/stability matters;
- unattended server generation is required;
- audit/billing must be clean;
- customer data sensitivity requires controlled backend credentials;
- the subscription bridge becomes brittle or manual.

## Failure Modes

Plan for:

- expired login;
- UI/API behavior change in the bridge;
- rate or usage cap;
- unavailable model;
- captcha/human verification;
- session tied to local machine;
- provider returns less structured output than expected.

The system should mark the run as `provider_unavailable` or `needs_reconnect`, not continue with hidden degraded behavior.
