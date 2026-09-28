"""Build the project hub page (hub/hub.html) from docs/SPEC.md, docs/STATS_GUIDE.md and hub/private/status_seed.json.
The spec is the single source of truth; the hub renders it and overlays live status from the artifact db.
The stats guide renders as its own rail group ("Stats modules"), above the specification."""
import json, re, markdown, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = (ROOT / "docs" / "SPEC.md").read_text()
plan_path = ROOT / "docs" / "private" / "PLAN.md"
if plan_path.exists():
    plan = plan_path.read_text()
    plan = plan[plan.index("\n## "):]                      # sections only (drop the file's H1 and preamble)
    spec = spec + "\n\n" + plan
guide_path = ROOT / "docs" / "STATS_GUIDE.md"
guide = guide_path.read_text() if guide_path.exists() else ""
seed = json.loads((ROOT / "hub" / "private" / "status_seed.json").read_text())

def render(text, cls):
    """Markdown with protected TeX -> (intro_html, nav [(id, title, [(sub_id, sub_title)])], sections_html)."""
    store = []
    def keep(m, display):
        store.append((m.group(1), display)); return f"MATHTOKEN{len(store)-1}X"
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(m, True), text, flags=re.S)
    text = re.sub(r"(?<![\\$])\$([^$\n]+?)\$", lambda m: keep(m, False), text)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "def_list", "sane_lists"],
                           extension_configs={"toc": {"permalink": False}})
    body = md.convert(text)
    def restore(m):
        tex, disp = store[int(m.group(1))]; tex = html.escape(tex.strip(), quote=False)
        return f'<div class="arithmatex">\\[{tex}\\]</div>' if disp else f'<span class="arithmatex">\\({tex}\\)</span>'
    body = re.sub(r"MATHTOKEN(\d+)X", restore, body)
    parts = re.split(r'(?=<h2 id=")', body)                 # one <section> per H2 so the rail can navigate
    intro, secs = parts[0], parts[1:]
    nav, sections = [], []
    for s in secs:
        m = re.match(r'<h2 id="([^"]+)">(.*?)</h2>', s)
        sid, title = m.group(1), re.sub("<[^>]+>", "", m.group(2))
        subs = [(i, re.sub("<[^>]+>", "", t).split("(")[0].strip()) for i, t in re.findall(r'<h3 id="(fn-[^"]+)">(.*?)</h3>', s)]
        nav.append((sid, title, subs))
        sections.append(f'<section class="{cls}" id="{sid}">{s}</section>')
    return intro, nav, "\n".join(sections)

def navhtml(nav):
    out = []
    for i, t, subs in nav:
        out.append(f'<a href="#{i}">{html.escape(t)}</a>')
        out += [f'<a class="sub" href="#{j}">{html.escape(u)}</a>' for j, u in subs]
    return "\n".join(out)

intro, nav, sections = render(spec, "spec")
g_intro, g_nav, g_sections = render(guide, "spec guide") if guide else ("", [], "")
g_intro = re.sub(r"<h1[^>]*>.*?</h1>", "", g_intro, flags=re.S)   # the page supplies its own heading
tpl = (ROOT / "hub" / "template.html").read_text()
out = (tpl.replace("{{NAV}}", navhtml(nav))
          .replace("{{INTRO}}", intro)
          .replace("{{SECTIONS}}", sections)
          .replace("{{GUIDE_NAV}}", navhtml(g_nav))
          .replace("{{GUIDE_INTRO}}", g_intro)
          .replace("{{GUIDE}}", g_sections)
          .replace("{{SEED}}", json.dumps(seed).replace("</", "<\\/")))
(ROOT / "hub" / "hub.html").write_text(out)
print("hub.html", len(out) // 1024, "KB,", len(nav), "spec sections,", len(g_nav), "guide sections")
