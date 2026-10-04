import json, os, glob, time, sys
from datetime import datetime
root = os.path.expanduser("~/.claude/projects")
cutoff = time.time() - 45*86400
markers = {"code": "You are a specialist code reviewer", "doc": "document reviewer"}
rows = []
for f in glob.glob(root + "/**/*.jsonl", recursive=True):
    try:
        if os.path.getmtime(f) < cutoff: continue
    except OSError: continue
    try:
        fh = open(f, errors="ignore")
    except OSError: continue
    with fh:
        for line in fh:
            if '"tool_use"' not in line or ('specialist code reviewer' not in line and 'document reviewer' not in line): continue
            try: d = json.loads(line)
            except Exception: continue
            msg = d.get("message") or {}
            content = msg.get("content")
            if not isinstance(content, list): continue
            usage = msg.get("usage") or {}
            for c in content:
                if c.get("type") != "tool_use": continue
                inp = c.get("input") or {}
                p = inp.get("prompt") or ""
                kind = "code" if markers["code"] in p else ("doc" if "document reviewer" in p.lower() else None)
                if not kind: continue
                rows.append((f, d.get("timestamp"), d.get("requestId") or msg.get("id"), kind, len(p.encode()), usage.get("output_tokens")))
# group by message id (one assistant turn may hold several spawns)
from collections import defaultdict
turns = defaultdict(list)
for r in rows: turns[(r[0], r[2])].append(r)
print("spawn prompts found:", len(rows), "in", len({r[0] for r in rows}), "files")
by_kind = defaultdict(list)
for r in rows: by_kind[r[3]].append(r[4])
for k, v in by_kind.items():
    v.sort(); n=len(v)
    print(f"{k}: n={n} median_bytes={v[n//2]} p90={v[int(n*0.9)]} max={v[-1]}")
print("recent turns (file-tail, ts, kind, n_spawns, total_prompt_bytes, msg_output_tokens):")
for key, rs in sorted(turns.items(), key=lambda kv: kv[1][0][1] or "")[-25:]:
    print(os.path.basename(key[0])[:8], rs[0][1], rs[0][3], len(rs), sum(r[4] for r in rs), rs[0][5])
