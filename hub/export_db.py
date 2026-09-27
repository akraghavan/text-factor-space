"""Write one JSON file per db document from hub/private/status_seed.json, plus a writes manifest for ArtifactData batch."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / "hub" / "dbsync"; OUT.mkdir(exist_ok=True)
seed = json.loads((ROOT / "hub" / "private" / "status_seed.json").read_text())
only = set(sys.argv[1:])  # optional: restrict to collections
writes = []
def put(coll, did, data):
    if only and coll not in only: return
    p = OUT / f"{coll.replace('/','_')}__{did}.json"; p.write_text(json.dumps(data, ensure_ascii=False))
    writes.append({"op": "set", "collection": coll, "doc_id": did, "file_path": str(p)})
for k in ("stages", "tasks", "decisions", "milestones"):
    for d in seed[k]:
        did = d.get("id") or d.get("key"); put(k, did, {kk: v for kk, v in d.items() if kk != "id"})
put("meta", "summary", {"updated": seed["updated"], "headline": seed["headline"], "next": seed["next"]})
put("meta", "log", {"entries": seed["log"]})
(OUT / "writes.json").write_text(json.dumps(writes, indent=0))
print(len(writes), "writes")
