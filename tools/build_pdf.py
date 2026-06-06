#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总 README + docs/01-14 为单一 PDF（中文，含封面/目录/页码/内部链接）。"""
import re, glob, os, datetime
import markdown
from weasyprint import HTML

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 收集文档（README 在前，docs 按编号排序） ----
files = [os.path.join(ROOT, "README.md")]
files += sorted(glob.glob(os.path.join(ROOT, "docs", "*.md")),
                key=lambda p: os.path.basename(p))

def anchor_for(path):
    b = os.path.basename(path)
    if b == "README.md":
        return "doc-00"
    m = re.match(r"(\d{2})-", b)
    return f"doc-{m.group(1)}" if m else "doc-" + re.sub(r"\W", "", b)

def title_of(path, text):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else os.path.basename(path)

# ---- markdown 链接重写：.md -> 内部锚点 ----
def rewrite_md_links(text):
    def repl(m):
        label, target = m.group(1), m.group(2).strip()
        frag = ""
        t = target
        if "#" in t:
            t, frag = t.split("#", 1)
        mm = re.match(r"(?:\./)?(?:docs/)?(\d{2})-.*\.md$", t)
        if mm:
            return f"[{label}](#doc-{mm.group(1)})"
        if re.search(r"README\.md$", t):
            return f"[{label}](#doc-00)"
        if t.endswith(".html") or t.startswith("prototype"):
            return label  # 原型为交互文件，PDF 中转为纯文本
        return m.group(0)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)

md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])

sections, toc = [], []
for f in files:
    raw = open(f, encoding="utf-8").read()
    # 图片路径：docs 内用 ../screenshots（GitHub 友好）；PDF 以 ROOT 为 base_url，改为 screenshots/
    raw = raw.replace("../screenshots/", "screenshots/")
    a = anchor_for(f)
    toc.append((a, title_of(f, raw)))
    md.reset()
    html = md.convert(rewrite_md_links(raw))
    sections.append(f'<section class="doc" id="{a}">{html}</section>')

# ---- 目录 HTML ----
toc_html = '<section class="toc-page"><h1 class="toc-h">目录</h1><ul class="toc">'
for a, t in toc:
    toc_html += f'<li><a href="#{a}">{t}</a></li>'
toc_html += "</ul></section>"

today = datetime.date.today().strftime("%Y-%m-%d")
cover = f'''<section class="cover">
  <div class="cover-top">
    <div class="cover-badge">PRODUCT STRATEGY · v1.0</div>
    <div class="cover-brand">YYT-Store</div>
  </div>
  <div class="cover-mid">
    <h1 class="cover-title">门店数据分析平台</h1>
    <div class="cover-sub">产品规划与发展文档</div>
    <div class="cover-line"></div>
    <div class="cover-desc">面向存量门店经营与发展的<br><b>「多维数据分析 ＋ AI 决策」</b>平台</div>
    <div class="cover-spine">
      <span class="sp">外部数据</span><span class="sp-ar">→</span>
      <span class="sp">会员数据</span><span class="sp-ar">→</span>
      <span class="sp">经营数据</span>
    </div>
    <div class="cover-spine-cap">产品主线 · 三层数据递进 · 由外到内逐层解锁</div>
    <div class="cover-tags">
      <span class="ct">移动端优先</span><span class="ct">AI 优先</span>
      <span class="ct">管理端 · 执行端</span><span class="ct">五圈层模型</span>
      <span class="ct">点位 vs 经营</span>
    </div>
  </div>
  <div class="cover-meta">汇总文档 {len(files)} 篇　·　含交互原型截图　·　{today}</div>
</section>'''

CSS = '''
@page {
  size: A4; margin: 20mm 18mm 18mm 18mm;
  @bottom-center { content: counter(page); font-size: 9pt; color: #9AA0AE; font-family: "WenQuanYi Zen Hei"; }
  @top-right { content: "YYT-Store · 门店数据分析平台"; font-size: 8pt; color: #C2C7D2; font-family: "WenQuanYi Zen Hei"; }
}
@page cover { margin: 0; @bottom-center { content: none; } @top-right { content: none; } }
@page toc  { @top-right { content: none; } }
* { font-family: "WenQuanYi Zen Hei", sans-serif; }
body { color: #20242E; font-size: 10.5pt; line-height: 1.75; }

/* cover */
.cover { page: cover; height: 297mm; background: linear-gradient(155deg,#2a3766 0%,#1b2240 55%,#121728 100%);
  color:#fff; padding: 30mm 24mm; display:flex; flex-direction:column; justify-content:space-between; }
.cover-top { display:flex; justify-content:space-between; align-items:center; }
.cover-brand { font-size:13pt; font-weight:800; color:#9fb2ff; letter-spacing:1px; }
.cover-badge { font-size:8.5pt; letter-spacing:3px; color:#9fb2ff; border:1px solid #46568c;
  padding:5px 12px; border-radius:20px; }
.cover-mid { }
.cover-title { font-size:42pt; font-weight:800; line-height:1.14; margin:0;
  color:#fff; border:0; padding:0; }
.cover-sub { font-size:16pt; color:#aeb8d6; margin-top:12px; }
.cover-line { width:64px; height:4px; background:linear-gradient(90deg,#6a8bff,#3056D3); border-radius:3px; margin:26px 0; }
.cover-desc { font-size:13pt; color:#d3d9ea; line-height:1.9; }
.cover-desc b { color:#fff; }
.cover-spine { margin-top:28px; }
.cover-spine .sp { font-size:11pt; font-weight:800; color:#fff; background:rgba(108,139,255,.20);
  border:1px solid #4a5b95; padding:8px 16px; border-radius:24px; }
.cover-spine .sp-ar { color:#8190c4; font-size:13pt; padding:0 8px; }
.cover-spine-cap { font-size:9pt; color:#8a96bb; margin-top:11px; letter-spacing:.5px; }
.cover-tags { margin-top:22px; }
.cover-tags .ct { display:inline-block; font-size:9pt; color:#b3bcda; border:1px solid #38426c;
  padding:4px 11px; border-radius:18px; margin:0 7px 8px 0; }
.cover-meta { font-size:9.5pt; color:#828daf; border-top:1px solid #2c365a; padding-top:14px; }

/* toc */
.toc-page { page: toc; }
.toc-h { font-size:22pt; color:#1E3A9E; border:0; margin:0 0 22px; }
ul.toc { list-style:none; padding:0; margin:0; }
ul.toc li { margin:0; }
ul.toc a { display:flex; align-items:baseline; text-decoration:none; color:#2B3242; font-size:11.5pt;
  padding:9px 0; border-bottom:1px dashed #E2E5EC; }
ul.toc a::after { content: leader('. ') target-counter(attr(href), page); color:#9AA0AE; font-size:10pt; }

/* doc sections */
.doc { break-before: page; }
h1 { font-size:19pt; color:#1E3A9E; font-weight:800; margin:0 0 4px; padding-bottom:9px;
  border-bottom:3px solid #3056D3; }
h2 { font-size:14pt; color:#21305e; font-weight:700; margin:24px 0 8px; padding-left:10px;
  border-left:4px solid #3056D3; }
h3 { font-size:11.5pt; color:#2B3242; font-weight:700; margin:16px 0 6px; }
p { margin:7px 0; }
a { color:#3056D3; text-decoration:none; }
strong, b { color:#1b2138; }
hr { border:0; border-top:1px solid #E6E9F0; margin:18px 0; }
blockquote { margin:10px 0; padding:9px 14px; background:#EFF3FF; border-left:4px solid #3056D3;
  border-radius:0 8px 8px 0; color:#33405e; font-size:10pt; }
ul, ol { margin:7px 0; padding-left:22px; }
li { margin:3px 0; }
code { background:#EEF0F5; color:#b03a2e; padding:1px 5px; border-radius:4px; font-size:9pt;
  font-family:"WenQuanYi Zen Hei Mono", monospace; }
pre { background:#1b2138; color:#dfe4f2; padding:13px 15px; border-radius:9px; overflow:hidden;
  font-size:8pt; line-height:1.5; white-space:pre; }
pre code { background:none; color:#dfe4f2; padding:0; font-family:"WenQuanYi Zen Hei Mono", monospace; }

/* tables */
table { width:100%; border-collapse:collapse; margin:12px 0; font-size:9.3pt; }
th { background:#2B3656; color:#fff; font-weight:600; text-align:left; padding:8px 9px; }
td { padding:7px 9px; border-bottom:1px solid #E6E9F0; vertical-align:top; }
tr:nth-child(even) td { background:#F7F8FB; }
table, tr, td, th { break-inside: avoid; }
h1, h2, h3 { break-after: avoid; }

/* 原型截图 */
img { border:1px solid #DDE1EA; border-radius:8px; break-inside: avoid; }
img.phone { width:52mm; display:inline-block; vertical-align:top; margin:5px 4px; }
img.wide  { width:100%; display:block; margin:10px auto; }
'''

full = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{cover}{toc_html}{''.join(sections)}</body></html>"
out = os.path.join(ROOT, "YYT-Store-产品规划文档.pdf")
HTML(string=full, base_url=ROOT).write_pdf(out, stylesheets=[__import__("weasyprint").CSS(string=CSS)])
print("PDF ->", out, "|", round(os.path.getsize(out)/1024), "KB")
