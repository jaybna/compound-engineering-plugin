# ce-code-review: Stage 4 "one parallel read-tool wave" leads to a truncated `cat` and about 10 wasted orchestrator turns

## Problem

The #1723 live eval recorded this as a follow-up, but nobody filed an issue for it.

`docs/plans/2026-09-15-review-spine-cost-eval-report.md:35`:

> turns 24 to 35 are twelve turns for what the plan expected to be two reads. The headless Claude orchestrator concatenated several large files into one `cat` call, the tool result was truncated, and it re-read the truncated tail and then the individual files: `subagent-template.md` was read three times and `dispatch-reviewers.md` twice. The baseline run showed the same pattern. This is a harness output limit, not a reference-load defect, and the fix would be one reference per read call at the Stage 4 pointer. Not changed in this PR; recorded as follow-up.

The instruction that leads to this is `skills/ce-code-review/references/dispatch-reviewers.md:61`:

> Read them and all selected persona prompt assets in one parallel read-tool wave rather than one turn per file.

"One wave" is meant to mean several read calls in one message. A headless Claude orchestrator read it as one shell command that joins the files, and that output hit the tool-result limit.

## Why it matters

On the full path every orchestrator turn replays the whole context. The same eval measured 12.5M cache-read tokens over 68 turns, which is about 180k per turn. About 10 surplus turns therefore cost roughly 1.8M cache-read tokens and an estimated 1-2 minutes on every full Claude review. It showed up in both the baseline and the post-#1723 run, so it is systematic. Codex (29 tool calls) did not show it.

## Proposal

State the condition at the Stage 4 pointer: each reference and persona asset is read by its own file-read call, and all of those calls are issued together in one message. Files are never joined in one shell output. Serial hosts keep reading one file per turn, as they do today.

To keep it from coming back, the existing live review cell's trace grading could assert that each Stage 4 reference is read at most once and that no multi-file shell read occurs. That uses the same tool-trace check the eval already ran by hand.

## Quality impact

None to findings: the same files are read, and only the way they are read changes.

## Verification

Re-run the `review-live-full` cell on Claude and compare against the 68-turn baseline and the turns 24-35 window in the report.

---
Drafted with Claude Code (claude-opus-5-5) while reviewing CE for cycle-time improvements. Evidence was checked against `9af474a7`.
