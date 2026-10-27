# Model per etap

| Etap | Claude Code | Codex |
|---|---|---|
| Rekonesans repo | Explore na sonnet; synteza opus high | explorer: gpt-6-luna high |
| Brainstorm + spec | fable (jeśli w /model), inaczej opus xhigh | gpt-6-astra, start low, podnoś do high |
| Krytyka specu/planu (plan-critique) | opus xhigh, świeży kontekst | gpt-6-astra high |
| Plan + tasks | opus high | gpt-6.1-sol high |
| Implementacja zadania | sonnet high (subagent) | worker: gpt-6.1-sol high |
| Zadanie mechaniczne | haiku / sonnet medium | gpt-6-luna high |
| Review A (poprawność) | /code-review high | codex review (sol) |
| Review B (drugi model) | oba: /codex:adversarial-review (astra); samo Claude: cross-reviewer opus xhigh | reviewer: gpt-6-astra high |
| Security | plugin Anthropic security | Codex Security plugin |
| Debugging | opus xhigh | gpt-6-astra high |
| Triage, chores, automations | haiku / sonnet low | gpt-6-luna |

Zasady:
- Autor i reviewer: inny model albo inna rodzina modeli.
- Claude: sesja główna opus; subagenci domyślnie sonnet; reviewer xhigh.
- Codex (wg oficjalnych docs): gpt-6.1-sol do wymagających agentów, gpt-6-luna do szybkich i wąskich; Astra zaczynaj od low i podnoś.
- xhigh/max tylko na spec, krytykę planu i trudny debugging.
