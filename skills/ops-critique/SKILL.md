---
name: ops-critique
description: Adversarial critique of an OpenSpec proposal, design and tasks by a different model, before any code. Use after /opsx:propose and before implementation.
argument-hint: <change-id>
---
Input: openspec/changes/<id>/proposal.md, design.md, specs/**, tasks.md. Concatenate them.
Critic prompt:
  "You are a harsh reviewer of a software change plan. Find logical gaps, missing edge cases, untestable requirements, contradictions between proposal, specs, design and tasks, risky assumptions, missing non-goals, and tasks too large for one context. Do not praise. Output sections: critical, major, minor, open questions."
Critic by variant (read .aidevops/variant):
- claude-codex: `codex exec -m gpt-6-astra -c model_reasoning_effort=high "<critic prompt + concatenated files>"`
- claude: cross-reviewer agent in a fresh context
- codex: reviewer agent (gpt-6-astra)
Save the raw output to openspec/changes/<id>/critique.md. Summarize critical and major items to the user as concrete edits to the artifacts. Apply only what the user approves.
