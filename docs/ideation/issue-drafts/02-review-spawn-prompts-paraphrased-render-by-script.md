# ce-code-review / ce-doc-review: reviewer spawn prompts in real runs are 1-5 KB, not the ~30 KB the dispatch spec asks for

## Problem

Both review skills tell the orchestrator to build each reviewer's prompt by inlining shared material:

- `skills/ce-code-review/references/dispatch-reviewers.md:63-67` lists what each persona subagent receives: "1. Their persona file content ... 2. Shared diff-scope rules ... 3. The JSON output contract ..." All of it goes through `references/subagent-template.md`, whose template block is 12,525 bytes. Persona files are 5-10 KB, `diff-scope.md` is 4,954 bytes and `findings-schema.json` is 8,192 bytes. A faithful spawn prompt is therefore about 32-36 KB.
- `skills/ce-doc-review/references/dispatch.md:9` says: "read `references/personas/<reviewer-name>.md` and pass its full content as `{persona_file}`". That template block is 23,064 bytes before the persona and document slice.

That is not what orchestrators send. I measured every reviewer spawn prompt in my own local Claude Code transcripts from the last 45 days. That was 4 sessions on CE 3.24.0, 3.26.3 and 3.27.0. All three versions specify the same ~12.5 KB code-review template block that main has today.

| Skill | Spawns | Median bytes | p90 | Max |
|---|---|---|---|---|
| ce-code-review | 71 | 4,509 | 7,600 | 9,085 |
| ce-doc-review | 35 | 3,312 | 4,484 | 4,831 |

I checked the structure of six code-review prompts. None contained the template's calibration paragraph ("Find significant problems that affect the requested outcome ..."), and none pointed the reviewer at its persona file path. Only one had the template's XML sections. The orchestrator appears to be paraphrasing the contract instead of passing it.

## Why it matters

There are two costs, and they pull in opposite directions:

- **Quality.** Reviewers may run without the persona's failure modes, suppress conditions and calibration, and those are the parts that make the lenses distinct.
- **Speed.** Following the spec literally would make the orchestrator generate about 8-9k output tokens per reviewer, in series, before reviewers can start. Output tokens are the slowest tokens. Reading the persona and shared files into the orchestrator also grows the context that every later turn replays. That is the "per-turn context growth" follow-up named in `docs/solutions/skill-design/review-cost-is-in-entering-the-spine-not-the-findings.md`.

So today the run is fast because the orchestrator cuts corners. The faithful path is the slow one.

## Proposal

Make the faithful path the cheap path. A bundled stdlib script, beside `run-log.py` and `findings-mechanics.py`, assembles each selected reviewer's full prompt from the template, persona, scope rules, schema and run variables, and writes it to `<run-dir>/prompts/<reviewer>.md`. The spawn prompt becomes a short pointer: read this file first, then review. The orchestrator then has no need to read persona or template files into its own context at Stage 4.

This follows the repo's own learning `docs/solutions/skill-design/pass-paths-not-content-to-subagents.md`, which calls orchestrator read-then-inline a refactor signal.

If skipped reads are a concern, the script can stamp a nonce into each prompt file and have the reviewer echo it in its artifact. The existing findings helper can then reject a missing nonce. That catches a skip mechanically instead of relying on prose. A host whose subagents cannot read files keeps today's inline path.

## How to reproduce the measurement

Scan Claude Code session JSONL for assistant `tool_use` blocks whose `input.prompt` starts with "You are a specialist code reviewer" (code) or contains "document reviewer" (doc), and record `len(prompt.encode())`. I can share the script.

## Caveats

This is one user's sessions, on Claude Code only, so it would be worth checking against your own transcripts or the eval cells before acting. I did not measure finding quality directly. The quality concern is inferred from what the prompts lacked.

---
Drafted with Claude Code (claude-opus-5-5) while reviewing CE for cycle-time improvements. Evidence was checked against `9af474a7`. The transcript measurements are from my local sessions; only sizes and structure were inspected.
