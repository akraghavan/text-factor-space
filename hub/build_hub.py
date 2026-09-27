"""Build the project hub page (hub/hub.html) from docs/SPEC.md + hub/private/status_seed.json.
The spec is the single source of truth; the hub renders it and overlays live status from the artifact db."""
import json, re, markdown, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = (ROOT / "docs" / "SPEC.md").read_text()
plan_path = ROOT / "docs" / "private" / "PLAN.md"
if plan_path.exists():
    plan = plan_path.read_text()
    plan = plan[plan.index("\n## "):]                      # sections only (drop the file's H1 and preamble)
    spec = spec + "\n\n" + plan
seed = json.loads((ROOT / "hub" / "private" / "status_seed.json").read_text())
# protect math from the markdown parser, restore afterwards
store = []
def keep(m, display):
    store.append((m.group(1), display)); return f"MATHTOKEN{len(store)-1}X"
spec = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(m, True), spec, flags=re.S)
spec = re.sub(r"(?<![\\$])\$([^$\n]+?)\$", lambda m: keep(m, False), spec)
md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "def_list", "sane_lists"],
                       extension_configs={"toc": {"permalink": False}})
body = md.convert(spec)
def restore(m):
    tex, disp = store[int(m.group(1))]; tex = html.escape(tex.strip(), quote=False)
    return f'<div class="arithmatex">\\[{tex}\\]</div>' if disp else f'<span class="arithmatex">\\({tex}\\)</span>'
body = re.sub(r"MATHTOKEN(\d+)X", restore, body)
# split into <section> per H2 so the rail can navigate
parts = re.split(r'(?=<h2 id=")', body)
intro, secs = parts[0], parts[1:]
nav = []
sections = []
for s in secs:
    m = re.match(r'<h2 id="([^"]+)">(.*?)</h2>', s)
    sid, title = m.group(1), re.sub("<[^>]+>", "", m.group(2))
    nav.append((sid, title))
    sections.append(f'<section class="spec" id="{sid}">{s}</section>')
tpl = (ROOT / "hub" / "template.html").read_text()
navhtml = "\n".join(f'<a href="#{i}">{html.escape(t)}</a>' for i, t in nav)
out = (tpl.replace("{{NAV}}", navhtml)
          .replace("{{INTRO}}", intro)
          .replace("{{SECTIONS}}", "\n".join(sections))
          .replace("{{SEED}}", json.dumps(seed).replace("</", "<\\/")))
(ROOT / "hub" / "hub.html").write_text(out)
print("hub.html", len(out) // 1024, "KB,", len(nav), "sections")
