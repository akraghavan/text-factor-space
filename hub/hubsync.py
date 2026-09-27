"""Diff hub/private/status_seed.json (desired state) against a dump of the live artifact db and
emit ArtifactData batch writes, pinned to the versions last read.
Usage: python hub/hubsync.py <live_dump_dir> <versions.json>  ->  hub/dbsync/writes.json
User-owned fields are never overwritten: tasks.done/doneAt (unless the seed marks a task done),
decisions.answer/status/answeredAt (unless the seed resolves a decision that has no answer from Abhi)."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / "hub" / "dbsync"; OUT.mkdir(exist_ok=True)
live_dir = pathlib.Path(sys.argv[1]); versions = json.loads(pathlib.Path(sys.argv[2]).read_text())
seed = json.loads((ROOT / "hub" / "private" / "status_seed.json").read_text())
def live(coll, did):
    p = live_dir / coll / f"{did}.json"
    return json.loads(p.read_text()) if p.exists() else None
writes = []
def emit(op, coll, did, data):
    p = OUT / f"{coll}__{did}.json"; p.write_text(json.dumps(data, ensure_ascii=False))
    w = {"op": op, "collection": coll, "doc_id": did, "file_path": str(p)}
    v = versions.get(f"{coll}/{did}")
    if v is not None: w["if_version"] = v
    writes.append(w)
for coll in ("stages", "milestones"):
    for d in seed[coll]:
        did = d.get("id") or d.get("key"); data = {k: v for k, v in d.items() if k != "id"}
        if live(coll, did) != data: emit("set", coll, did, data)
for d in seed["tasks"]:
    did = d["id"]; cur = live("tasks", did); mine = {k: v for k, v in d.items() if k not in ("id", "done", "doneAt")}
    if cur is None: emit("set", "tasks", did, {**mine, "done": d.get("done", False)}); continue
    if d.get("done") and not cur.get("done"): mine.update(done=True, doneAt=d.get("doneAt"))
    if any(cur.get(k) != v for k, v in mine.items()): emit("update", "tasks", did, mine)
for d in seed["decisions"]:
    did = d["id"]; cur = live("decisions", did); mine = {k: d[k] for k in ("question", "recommendation", "order") if k in d}
    if cur is None: emit("set", "decisions", did, {k: v for k, v in d.items() if k != "id"}); continue
    if d.get("status") == "resolved" and cur.get("status") != "resolved":
        mine["status"] = "resolved"
        if not cur.get("answer"): mine["answer"] = d.get("answer", "")
    if any(cur.get(k) != v for k, v in mine.items()): emit("update", "decisions", did, mine)
summ = {"updated": seed["updated"], "headline": seed["headline"], "next": seed["next"], "synced": seed.get("synced", seed["updated"])}
if live("meta", "summary") != summ: emit("set", "meta", "summary", summ)
logd = {"entries": seed["log"]}
if live("meta", "log") != logd: emit("set", "meta", "log", logd)
(OUT / "writes.json").write_text(json.dumps(writes))
print(len(writes), "writes:", " ".join(f"{w['op']}:{w['collection']}/{w['doc_id']}" for w in writes))
