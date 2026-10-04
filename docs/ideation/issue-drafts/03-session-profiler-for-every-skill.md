# Measure where every skill's time goes from host transcripts (zero runtime cost), so measurement-gated speedups can be decided

## Problem

Only `ce-code-review` can show where its wall-clock goes. It writes `stages.jsonl` through `skills/ce-code-review/scripts/run-log.py` (#1723). No other skill records stage time. That includes `ce-plan`, `ce-doc-review`, `ce-work`, `lfg` and `ce-brainstorm`. The skill-eval harness records `exitCode, timedOut, stdout_bytes, stderr_bytes, process_outcome` per cell, with no duration or tokens (`tests/skill-eval-cell/run.ts:429-436`).

Several speed decisions are now explicitly waiting on numbers:

- #1815: "Two possible gates wait until they're measured: re-running only the affected `ce-doc-review` reviewers in round 2, and running `ce-simplify-code` inline on small scopes."
- `docs/solutions/skill-design/review-cost-is-in-entering-the-spine-not-the-findings.md` lists per-stage instrumentation beyond code review as an open follow-up. It also says: "Before tuning a threshold, attribute the cost by stage from a real run."
- The #1723 plan deferred a cross-run consumer because "nothing consumes it yet".
- The 12-turn Stage 4 re-read in the #1723 eval report was found only by hand-grading a tool trace.

As a user, I tried to answer "where does our CE time go?" from my own transcripts and could not separate agent time from human think-time without writing custom parsing.

## Why not add run-log.py to every skill

`lfg`'s step boundaries are skill invocations, not shell calls. The "fold the boundary into a shell call the step already makes" rule (`skills/ce-code-review/references/scope.md:168`) therefore has nothing to fold into, and each log call would be an extra turn at full orchestrator context. That is the cost the #1723 plan warned against ("The instrumentation must not spend what the split saves").

## Proposal

Add a repo-level, read-only profiler under `scripts/`. It is maintainer tooling and does not ship in any skill. For each CE skill invocation in a host session transcript, it prints:

- wall-clock split into agent time and human think-time (gaps that end in a user turn or a question answer)
- assistant turns and cache-read, cache-write and output tokens, where the host records them
- the longest tool and subagent waits
- files read more than once

`skills/ce-compound/scripts/session-history/extract-metadata.py` and `extract-skeleton.py` already detect Claude, Codex, Cursor, Pi and omp transcripts and parse their records. They do not compute timing or usage today, but their platform detection is the natural starting point.

Optional and small: add `duration_ms` to each skill-eval cell record as a report-only column, with no thresholds.

## Quality impact

None to skills: the tool is read-only, runs outside skill runs and adds no turns. Transcript formats drift, so it should fail soft on an unknown format and be pinned with one small fixture per host.

## What it unblocks

It gives a direct answer to #1815's two deferred gates. It also gives the evidence needed for or against a `ce-doc-review` depth gate, overlapping doc-review synthesis with the cross-model peer tail, and starting the code-review peer earlier. And it lets anyone who reports "skill X feels slow" attach a reproducible table instead of an impression.

---
Drafted with Claude Code (claude-opus-5-5) while reviewing CE for cycle-time improvements. Evidence was checked against `9af474a7`.
