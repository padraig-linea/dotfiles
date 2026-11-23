#!/usr/bin/env python3
"""
Claude Code hook: PreToolUse, matcher "ExitPlanMode".

Fires when Claude finishes a plan and asks for approval. Renders the plan's
Markdown into a standalone HTML document next to the plan's .md file
(e.g. plans/foo.md -> plans/foo.html) and opens it in the browser, so the
plan can be reviewed before approving.

The Markdown renderer uses only the standard library, so the hook keeps
working across Python upgrades. (An earlier version depended on the
`markdown` package and silently fell back to raw text when it was absent.)
It covers what Claude's plans use: ATX headings, paragraphs, fenced code
blocks, nested bullet / numbered / task lists, pipe tables, blockquotes,
horizontal rules, and inline code, bold, italic, strikethrough, links and
images.

Executive summary (REQUIRE_SUMMARY): the plan's first h2 must be
"Executive summary" (the rule lives in ~/.claude/CLAUDE.md). If it is
missing, the hook denies ExitPlanMode with a reason, Claude adds the
section and calls ExitPlanMode again. In the HTML the summary renders as a
tinted, unnumbered panel above the numbered sections.

Page features:
  * Every top-level h2 starts a collapsible section (click the heading to
    fold it). h2/h3 are numbered 1, 1.1, ... unless the heading already
    starts with a number. A sticky table of contents lists them, highlights
    the section on screen, and has Collapse all / Expand all.
  * ```mermaid fences become diagrams.
  * Fenced code with a language tag is syntax-highlighted (highlight.js
    "common" build, which includes C, C++, Python, Bash, Diff, JSON, YAML,
    Makefile; plus the PowerShell and CMake modules). Every code block gets
    a Copy button.

Mermaid and highlight.js load from hooks/vendor/ (cached copies, work
offline) with the jsDelivr CDN as fallback, and only when the plan needs
them. To update either, replace the vendor files and bump the version
constant below.

Set PLAN_TO_HTML_NO_BROWSER=1 to skip opening the browser (used by tests).
Never blocks plan approval: always exits 0.
"""
import html
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

OPEN_IN_BROWSER = True  # pop the rendered plan open automatically
REQUIRE_SUMMARY = True  # deny ExitPlanMode when the plan's first h2 is not "Executive summary"
SUMMARY_TITLE = "executive summary"
SUMMARY_REASON = (
    "Plan rejected by the plan_to_html hook: the plan file must start with an "
    "'## Executive summary' section directly under the title (the first h2). "
    "Contents: two to four sentences on what the plan does and why; a 'Key decisions' "
    "list with one bullet per decision naming the choice, the rejected alternative and "
    "the reason; an 'Out of scope / risks' line if any. Length scales with the plan: "
    "around 150 words for a small plan, longer for a large one. Overview and main "
    "decisions only, not step-by-step detail; a diagram or short code snippet is fine "
    "where it explains a decision. Add it to the plan file, then call ExitPlanMode again."
)

VENDOR = Path(__file__).resolve().parent / "vendor"
MERMAID_VERSION = "11.17.2"
MERMAID_CDN = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
HLJS_VERSION = "11.12.0"
HLJS_CDN = f"https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@{HLJS_VERSION}/build"
HLJS_EXTRA_LANGUAGES = ("powershell", "cmake")  # not in the common build

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { --fg:#1f2328; --bg:#ffffff; --muted:#59636e; --code:#f6f8fa; --border:#d1d9e0; --link:#0969da; }
  @media (prefers-color-scheme: dark) {
    :root { color-scheme: dark; --fg:#e6edf3; --bg:#0d1117; --muted:#9198a1; --code:#161b22; --border:#3d444d; --link:#4493f8; }
  }
  /* Full-width layout. Set --max-width to e.g. 1400px to cap the line length again. */
  body { --max-width: none;
         font-family: system-ui, sans-serif; color: var(--fg); background: var(--bg);
         max-width: var(--max-width); margin: 0 auto; padding: 0 2.5rem 2rem; line-height: 1.55; }
  body.has-toc { display: grid; grid-template-columns: 270px minmax(0, 1fr); gap: 0 2.5rem; }
  main { min-width: 0; padding-top: 1.5rem; }
  h1, h2 { border-bottom: 1px solid var(--border); padding-bottom: .3em; margin-top: 1.5em; }
  h3, h4 { margin-top: 1.3em; }
  .num { color: var(--muted); margin-right: .35em; }
  a { color: var(--link); }
  code, pre { font-family: Consolas, "Cascadia Code", monospace; background: var(--code); font-size: .92em; }
  code { padding: .1em .3em; border-radius: 4px; }
  pre { position: relative; padding: 1em; overflow-x: auto; border-radius: 6px; border: 1px solid var(--border); line-height: 1.4; }
  pre code { padding: 0; background: none; font-size: 1em; }
  pre code.hljs { padding: 0; background: transparent; }
  table { border-collapse: collapse; margin: 1em 0; display: block; width: max-content; max-width: 100%; overflow-x: auto; }
  th, td { border: 1px solid var(--border); padding: .4em .7em; vertical-align: top; }
  th { background: var(--code); text-align: left; }
  tbody tr:nth-child(even) { background: color-mix(in srgb, var(--code) 60%, var(--bg)); }
  blockquote { border-left: 4px solid var(--border); margin: 1em 0; padding: 0 1em; color: var(--muted); }
  hr { border: 0; border-top: 1px solid var(--border); margin: 2em 0; }
  li { margin: .15em 0; }
  li.task { list-style: none; margin-left: -1.4em; }
  li.task input { margin-right: .4em; }
  img { max-width: 100%; }
  .meta { color: var(--muted); font-size: .85em; margin-top: 0; }

  /* Collapsible h2 sections */
  details.section > summary { list-style: none; cursor: pointer; border-bottom: 1px solid var(--border);
                              margin-top: 1.5em; padding-bottom: .3em; }
  details.section > summary::-webkit-details-marker { display: none; }
  details.section > summary::before { content: "\\25BE"; display: inline-block; width: 1em; color: var(--muted); font-size: 1.3em; }
  details.section:not([open]) > summary::before { content: "\\25B8"; }
  details.section > summary h2 { display: inline; border: 0; margin: 0; padding: 0; }
  details.section > summary:hover h2 { color: var(--link); }
  /* Executive summary panel */
  details.section.summary { background: color-mix(in srgb, var(--link) 7%, var(--bg));
                            border: 1px solid color-mix(in srgb, var(--link) 30%, var(--border));
                            border-radius: 8px; padding: .3em 1.3em 1em; margin-top: 1.5em; }
  details.section.summary > summary { margin-top: .3em; border-bottom: 0; }
  details.section.summary > summary h2 { font-size: 1.25em; }
  details.section.summary > :last-child { margin-bottom: 0; }

  /* Table of contents */
  nav.toc { position: sticky; top: 0; align-self: start; max-height: 100vh; overflow-y: auto; box-sizing: border-box;
            font-size: .9em; padding: 1.5rem 1rem 1rem 0; border-right: 1px solid var(--border); }
  nav.toc ul { list-style: none; margin: 0; padding: 0; }
  nav.toc ul ul { padding-left: 1em; }
  nav.toc li { margin: 0; }
  nav.toc a { color: var(--fg); text-decoration: none; display: block; padding: .2em .5em; border-radius: 4px;
              border-left: 3px solid transparent; }
  nav.toc a:hover { background: var(--code); }
  nav.toc a.current { border-left-color: var(--link); color: var(--link); background: var(--code); }
  .toc-head { display: flex; gap: .4em; align-items: baseline; margin-bottom: .6em; color: var(--muted); font-weight: 600; }
  .toc-head span { flex: 1; }
  .toc-btn, .copy { font: inherit; font-size: .8em; color: var(--muted); background: var(--bg); border: 1px solid var(--border);
                    border-radius: 4px; padding: .1em .5em; cursor: pointer; }
  .toc-btn:hover, .copy:hover { color: var(--fg); }
  pre .copy { position: absolute; top: .5em; right: .5em; opacity: 0; transition: opacity .15s; }
  pre:hover .copy, pre .copy:focus { opacity: 1; }

  /* Diagrams */
  pre.mermaid { background: none; border: 0; text-align: center; }
  pre.mermaid.unrendered { background: var(--code); border: 1px solid var(--border); text-align: left; }
  pre.mermaid.unrendered::before { content: "Mermaid script not available; diagram source:"; display: block; color: var(--muted); margin-bottom: .6em; }

  @media (max-width: 1000px) {
    body.has-toc { display: block; }
    nav.toc { position: static; max-height: none; border-right: 0; border-bottom: 1px solid var(--border); padding-right: 0; }
  }
  @media print {
    nav.toc, .copy { display: none; }
    body.has-toc { display: block; }
  }
</style>
</head>
<body class="__BODYCLASS__">
__TOC__
<main>
<p class="meta">Generated __STAMP__ from __SOURCE__</p>
__BODY__
</main>
__SCRIPT__
</body>
</html>
"""

PAGE_SCRIPT = r"""<script>
(function () {
  var cfg = __CONFIG__;

  function loadScript(sources, onload, onfail) {
    var i = 0;
    (function next() {
      if (i >= sources.length) { if (onfail) onfail(); return; }
      var s = document.createElement("script");
      s.src = sources[i++];
      s.onload = onload;
      s.onerror = next;
      document.head.appendChild(s);
    })();
  }
  function loadCss(sources, media) {
    var i = 0;
    (function next() {
      if (i >= sources.length) return;
      var l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = sources[i++];
      if (media) l.media = media;
      l.onerror = function () { l.remove(); next(); };
      document.head.appendChild(l);
    })();
  }
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text);
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } finally { ta.remove(); }
    return Promise.resolve();
  }

  // Copy buttons on code blocks.
  document.querySelectorAll("pre:not(.mermaid)").forEach(function (pre) {
    var b = document.createElement("button");
    b.type = "button"; b.className = "copy"; b.textContent = "Copy";
    b.addEventListener("click", function () {
      var code = pre.querySelector("code") || pre;
      copyText(code.textContent.replace(/\n$/, "")).then(function () {
        b.textContent = "Copied";
        setTimeout(function () { b.textContent = "Copy"; }, 1500);
      });
    });
    pre.appendChild(b);
  });

  // Unfold the section that contains a link target.
  function reveal(id) {
    var t = id && document.getElementById(id);
    var d = t && t.closest("details");
    if (d) d.open = true;
  }
  if (location.hash) reveal(decodeURIComponent(location.hash.slice(1)));
  window.addEventListener("hashchange", function () { reveal(decodeURIComponent(location.hash.slice(1))); });

  // Table of contents: current-section highlight, Collapse/Expand all.
  var toc = document.querySelector("nav.toc");
  if (toc) {
    var links = {};
    toc.querySelectorAll("a[href^='#']").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    toc.addEventListener("click", function (e) {
      var a = e.target.closest("a[href^='#']");
      if (a) reveal(a.getAttribute("href").slice(1));
    });
    var heads = Array.prototype.slice.call(document.querySelectorAll("main h2[id], main h3[id]"));
    var current = null;
    function update() {
      var limit = window.scrollY + window.innerHeight / 4, best = null;
      heads.forEach(function (h) {
        if (h.offsetParent === null) return;  // inside a folded section
        if (h.getBoundingClientRect().top + window.scrollY <= limit) best = h;
      });
      if (!best) best = heads[0];
      if (current) current.classList.remove("current");
      current = best && links[best.id];
      if (current) current.classList.add("current");
    }
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
    toc.querySelectorAll(".toc-btn").forEach(function (b) {
      b.addEventListener("click", function () {
        var open = b.dataset.action === "expand";
        document.querySelectorAll("details.section").forEach(function (d) { d.open = open; });
        update();
      });
    });
  }

  if (cfg.mermaid) {
    loadScript(cfg.mermaid, function () {
      mermaid.initialize({
        startOnLoad: false,
        theme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "default"
      });
      mermaid.run();
    }, function () {
      document.querySelectorAll("pre.mermaid").forEach(function (el) { el.classList.add("unrendered"); });
    });
  }

  if (cfg.hljs) {
    loadCss(cfg.hljs.css.light, "(prefers-color-scheme: light)");
    loadCss(cfg.hljs.css.dark, "(prefers-color-scheme: dark)");
    loadScript(cfg.hljs.js, function () {
      var pending = cfg.hljs.extras.length;
      function go() {
        document.querySelectorAll('pre code[class*="language-"]').forEach(function (el) {
          try { hljs.highlightElement(el); } catch (e) {}
        });
      }
      if (!pending) { go(); return; }
      function done() { if (--pending === 0) go(); }
      cfg.hljs.extras.forEach(function (srcs) { loadScript(srcs, done, done); });
    });
  }
})();
</script>"""

# --------------------------------------------------------------------------
# Markdown -> HTML, standard library only
# --------------------------------------------------------------------------

_FENCE_RE = re.compile(r"^( {0,3})(`{3,}(?!.*`)|~{3,})[ \t]*(\S*)")
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
_HR_RE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
_QUOTE_RE = re.compile(r"^ {0,3}> ?(.*)$")
_LIST_RE = re.compile(r"^([ \t]*)([-*+]|\d{1,9}[.)])(?:([ \t]+)(.*)|[ \t]*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$")
_TASK_RE = re.compile(r"^\[([ xX])\](?:[ \t]+|$)")
_SETEXT_H1_RE = re.compile(r"^ {0,3}=+[ \t]*$")

_CODE_RE = re.compile(r"(?<!\\)(`+)(.+?)(?<!`)\1(?!`)", re.S)
_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|~<>\"'])")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_AUTOLINK_RE = re.compile(r"&lt;(https?://[^\s<>]+?)&gt;")
_URL_RE = re.compile(r"(?<![\w\"'=/>\x00])(https?://[^\s<>\"'\x00]+)")
_BOLD_ITALIC_RE = re.compile(r"\*\*\*(?!\s)(.+?)(?<!\s)\*\*\*", re.S)
_BOLD_RE = re.compile(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", re.S)
_BOLD_U_RE = re.compile(r"(?<!\w)__(?!\s)(.+?)(?<!\s)__(?!\w)", re.S)
_ITALIC_RE = re.compile(r"\*(?!\s)(.+?)(?<!\s)\*", re.S)
_ITALIC_U_RE = re.compile(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", re.S)
_STRIKE_RE = re.compile(r"~~(?!\s)(.+?)(?<!\s)~~", re.S)
_BREAK_RE = re.compile(r"(?: {2,}|\\)\n")
_PLACEHOLDER_RE = re.compile(r"\x00(\d+)\x00")

_SLUGS = {}


def _slug(text):
    s = re.sub(r"[`*_~\[\]()!]", "", text).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-") or "section"
    n = _SLUGS.get(s, 0)
    _SLUGS[s] = n + 1
    return s if n == 0 else f"{s}-{n}"


def _inline(text):
    """Render inline Markdown. Finished fragments are stashed behind
    placeholders so later passes cannot mangle them."""
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return f"\x00{len(stash) - 1}\x00"

    def attr(value):
        return value.replace('"', "&quot;")

    def code(m):
        c = m.group(2)
        if len(c) > 2 and c[0] == c[-1] == " " and c.strip():
            c = c[1:-1]
        return keep(f"<code>{html.escape(c)}</code>")

    def image(m):
        title = f' title="{attr(m.group(3))}"' if m.group(3) else ""
        return keep(f'<img src="{attr(m.group(2))}" alt="{attr(m.group(1))}"{title}>')

    def link(m):
        title = f' title="{attr(m.group(3))}"' if m.group(3) else ""
        return keep(f'<a href="{attr(m.group(2))}"{title}>') + m.group(1) + keep("</a>")

    def bare_url(m):
        url, trail = m.group(1), ""
        while url and url[-1] in ".,:;!?)":
            if url[-1] == ")" and url.count("(") >= url.count(")"):
                break
            trail, url = url[-1] + trail, url[:-1]
        return keep(f'<a href="{url}">{url}</a>') + trail

    text = _CODE_RE.sub(code, text)
    text = _ESCAPE_RE.sub(lambda m: keep(html.escape(m.group(1))), text)
    text = html.escape(text, quote=False)
    text = _IMAGE_RE.sub(image, text)
    text = _LINK_RE.sub(link, text)
    text = _AUTOLINK_RE.sub(lambda m: keep(f'<a href="{m.group(1)}">{m.group(1)}</a>'), text)
    text = _URL_RE.sub(bare_url, text)
    text = _BOLD_ITALIC_RE.sub(r"<strong><em>\1</em></strong>", text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _BOLD_U_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    text = _ITALIC_U_RE.sub(r"<em>\1</em>", text)
    text = _STRIKE_RE.sub(r"<del>\1</del>", text)
    text = _BREAK_RE.sub("<br>\n", text)

    for _ in range(4):
        if "\x00" not in text:
            break
        text = _PLACEHOLDER_RE.sub(lambda m: stash[int(m.group(1))], text)
    return text


def _indent_of(line):
    line = line.expandtabs(4)
    return len(line) - len(line.lstrip(" "))


def _dedent(line, cols):
    line = line.expandtabs(4)
    return line[min(cols, _indent_of(line)):]


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    # GFM unescapes \| before cell content is parsed, so it works inside code spans too.
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def _table_at(lines, i):
    """(header_cells, aligns) if a pipe table starts at lines[i], else None."""
    if "|" not in lines[i] or i + 1 >= len(lines) or not _TABLE_SEP_RE.match(lines[i + 1]):
        return None
    header, seps = _split_row(lines[i]), _split_row(lines[i + 1])
    if len(seps) != len(header):
        return None
    aligns = []
    for s in seps:
        if not re.fullmatch(r":?-+:?", s):
            return None
        if s.startswith(":") and s.endswith(":"):
            aligns.append("center")
        elif s.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("")
    return header, aligns


def _render_table(header, aligns, rows):
    def cell(tag, text, align):
        style = f' style="text-align:{align}"' if align else ""
        return f"<{tag}{style}>{_inline(text)}</{tag}>"

    width = len(header)
    parts = ["<table>", "<thead><tr>" + "".join(cell("th", h, a) for h, a in zip(header, aligns)) + "</tr></thead>"]
    if rows:
        parts.append("<tbody>")
        for row in rows:
            row = (row + [""] * width)[:width]
            parts.append("<tr>" + "".join(cell("td", c, a) for c, a in zip(row, aligns)) + "</tr>")
        parts.append("</tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def _starts_block(lines, i):
    line = lines[i]
    return bool(
        _FENCE_RE.match(line) or _HEADING_RE.match(line) or _HR_RE.match(line)
        or _QUOTE_RE.match(line) or _LIST_RE.match(line) or _table_at(lines, i)
    )


def _parse_list(lines, i):
    """Parse the list starting at lines[i]. Returns (html, next_index)."""
    n = len(lines)
    m = _LIST_RE.match(lines[i])
    indent = len(m.group(1).expandtabs(4))
    ordered = m.group(2)[0].isdigit()
    start = int(m.group(2)[:-1]) if ordered else 1
    items, loose, blank_before = [], False, False

    while i < n:
        m = _LIST_RE.match(lines[i])
        if not m or len(m.group(1).expandtabs(4)) != indent or m.group(2)[0].isdigit() != ordered:
            break
        if blank_before:
            loose = True
        gap = len(m.group(3).expandtabs(4)) if m.group(3) else 1
        content_indent = indent + len(m.group(2)) + gap
        item = [m.group(4) or ""]
        i += 1
        blanks = 0
        while i < n:
            cur = lines[i]
            if not cur.strip():
                blanks += 1
                i += 1
                continue
            if _indent_of(cur) <= indent:
                break
            if blanks:
                item.extend([""] * blanks)
                loose = True
                blanks = 0
            # Tolerate under-indented continuation (e.g. 2 spaces under "1. ").
            content_indent = min(content_indent, _indent_of(cur))
            item.append(_dedent(cur, content_indent))
            i += 1
        blank_before = blanks > 0
        items.append(item)

    tag = "ol" if ordered else "ul"
    attrs = f' start="{start}"' if ordered and start != 1 else ""
    parts = [f"<{tag}{attrs}>"]
    for item in items:
        while item and not item[-1].strip():
            item.pop()
        prefix = cls = ""
        t = _TASK_RE.match(item[0]) if item else None
        if t:
            checked = " checked" if t.group(1) in "xX" else ""
            prefix = f'<input type="checkbox" disabled{checked}> '
            cls = ' class="task"'
            item[0] = item[0][t.end():]
        body = _render_blocks(item, tight=not loose)
        if prefix and body.startswith("<p>"):
            body = "<p>" + prefix + body[3:]
            prefix = ""
        parts.append(f"<li{cls}>{prefix}{body}</li>")
    parts.append(f"</{tag}>")
    return "\n".join(parts), i


def _block_list(lines, tight=False):
    """Render lines as a list of block-level HTML fragments. `tight` drops
    <p> wrappers (used inside tight list items)."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        m = _FENCE_RE.match(line)
        if m:
            indent, fence, lang = len(m.group(1)), m.group(2), m.group(3)
            close = re.compile(rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$")
            body = []
            i += 1
            while i < n and not close.match(lines[i]):
                body.append(_dedent(lines[i], indent) if indent else lines[i])
                i += 1
            i += 1  # closing fence, or end of input
            code = html.escape("\n".join(body))
            if lang.lower() == "mermaid":
                # Mermaid reads the element's text and replaces it with an SVG.
                out.append(f'<pre class="mermaid">{code}</pre>')
                continue
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{code}{chr(10) if body else ''}</code></pre>")
            continue

        m = _HEADING_RE.match(line)
        if m:
            level, text = len(m.group(1)), m.group(2)
            out.append(f'<h{level} id="{_slug(text)}">{_inline(text)}</h{level}>')
            i += 1
            continue

        if _HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        if _QUOTE_RE.match(line):
            inner = []
            while i < n:
                m = _QUOTE_RE.match(lines[i])
                if m:
                    inner.append(m.group(1))
                elif lines[i].strip() and not _starts_block(lines, i):
                    inner.append(lines[i])  # lazy continuation
                else:
                    break
                i += 1
            out.append(f"<blockquote>\n{_render_blocks(inner)}\n</blockquote>")
            continue

        table = _table_at(lines, i)
        if table:
            header, aligns = table
            rows = []
            i += 2
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(_split_row(lines[i]))
                i += 1
            out.append(_render_table(header, aligns, rows))
            continue

        if _LIST_RE.match(line):
            fragment, i = _parse_list(lines, i)
            out.append(fragment)
            continue

        # Paragraph: runs until a blank line or the start of another block.
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not _starts_block(lines, i):
            if _SETEXT_H1_RE.match(lines[i]):
                text = "\n".join(para)
                out.append(f'<h1 id="{_slug(text)}">{_inline(text)}</h1>')
                para = None
                i += 1
                break
            para.append(lines[i])
            i += 1
        if para is not None:
            text = _inline("\n".join(para))
            out.append(text if tight else f"<p>{text}</p>")
    return out


def _render_blocks(lines, tight=False):
    return "\n".join(_block_list(lines, tight))


# --------------------------------------------------------------------------
# Document assembly: numbered headings, collapsible sections, contents
# --------------------------------------------------------------------------

_H23_RE = re.compile(r'^<h([23]) id="([^"]+)">(.*)</h\1>$', re.S)
_ALREADY_NUMBERED_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)+|\d+[.):])\s")


def render_document(text):
    """Returns (body_html, toc_html). Top-level h2 blocks become collapsible
    sections, h2/h3 get numbers, and the contents list links to them."""
    _SLUGS.clear()
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out, section, entries = [], None, []
    n2 = n3 = 0
    in_summary = False  # the executive summary is a tinted panel, left unnumbered

    def close_section():
        nonlocal section
        if section is not None:
            out.append("\n".join(section) + "\n</details>")
            section = None

    for block in _block_list(lines):
        m = _H23_RE.match(block)
        if not m:
            (section if section is not None else out).append(block)
            continue
        level, hid, inner = int(m.group(1)), m.group(2), m.group(3)
        plain = re.sub(r"<[^>]+>", "", inner)
        if level == 2:
            in_summary = n2 == 0 and _norm_heading(plain) == SUMMARY_TITLE
        if in_summary:
            num = None
        elif level == 2:
            n2, n3 = n2 + 1, 0
            num = str(n2)
        else:
            n3 += 1
            num = f"{n2}.{n3}" if n2 else str(n3)
        if num and not _ALREADY_NUMBERED_RE.match(plain):
            inner = f'<span class="num">{num}</span>{inner}'
            plain = f"{num} {plain}"
        heading = f'<h{level} id="{hid}">{inner}</h{level}>'
        entries.append((level, hid, plain))
        if level == 2:
            close_section()
            cls = "section summary" if in_summary else "section"
            section = [f'<details class="{cls}" open><summary>{heading}</summary>']
        else:
            (section if section is not None else out).append(heading)
    close_section()

    toc = _render_toc(entries) if len(entries) >= 2 else ""
    return "\n".join(out), toc


def _render_toc(entries):
    parts = ['<nav class="toc">',
             '<div class="toc-head"><span>Contents</span>'
             '<button type="button" class="toc-btn" data-action="collapse">Collapse all</button>'
             '<button type="button" class="toc-btn" data-action="expand">Expand all</button></div>',
             "<ul>"]
    open_li = open_sub = False
    for level, hid, plain in entries:
        if level == 2:
            if open_sub:
                parts.append("</ul>")
                open_sub = False
            if open_li:
                parts.append("</li>")
            parts.append(f'<li><a href="#{hid}">{plain}</a>')
            open_li = True
        else:
            if not open_sub:
                if not open_li:
                    parts.append("<li>")
                    open_li = True
                parts.append("<ul>")
                open_sub = True
            parts.append(f'<li><a href="#{hid}">{plain}</a></li>')
    if open_sub:
        parts.append("</ul>")
    if open_li:
        parts.append("</li>")
    parts += ["</ul>", "</nav>"]
    return "\n".join(parts)


def render_markdown(text):
    """Body HTML only (used by tests)."""
    return render_document(text)[0]


def first_heading(text):
    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            return re.sub(r"[`*_]", "", m.group(2)).strip()
    return None


def _norm_heading(text):
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"[`*_]", "", html.unescape(text)).lower()).strip()


def first_h2(text):
    """Text of the first level-2 heading, ignoring headings inside fenced code."""
    fence = None
    for line in text.splitlines():
        if fence:
            if re.match(rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$", line):
                fence = None
            continue
        m = _FENCE_RE.match(line)
        if m:
            fence = m.group(2)
            continue
        m = _HEADING_RE.match(line)
        if m and len(m.group(1)) == 2:
            return m.group(2)
    return None


def has_summary(text):
    h2 = first_h2(text)
    return h2 is not None and _norm_heading(h2) == SUMMARY_TITLE


def _sources(local_name, cdn_url):
    """Script/style sources in load order: cached vendor copy, then CDN."""
    local = VENDOR / local_name
    return ([local.as_uri()] if local.is_file() else []) + [cdn_url]


def page_config(body_html):
    cfg = {"mermaid": None, "hljs": None}
    if '<pre class="mermaid">' in body_html:
        cfg["mermaid"] = _sources("mermaid.min.js", MERMAID_CDN)
    if '<pre><code class="language-' in body_html:
        cfg["hljs"] = {
            "js": _sources("highlight.min.js", f"{HLJS_CDN}/highlight.min.js"),
            "extras": [_sources(f"hljs-{lang}.min.js", f"{HLJS_CDN}/languages/{lang}.min.js")
                       for lang in HLJS_EXTRA_LANGUAGES],
            "css": {
                "light": _sources("hljs-github.min.css", f"{HLJS_CDN}/styles/github.min.css"),
                "dark": _sources("hljs-github-dark.min.css", f"{HLJS_CDN}/styles/github-dark.min.css"),
            },
        }
    return cfg


def build_page(plan_text, source_label, fallback_title):
    body, toc = render_document(plan_text)
    values = {
        "TITLE": html.escape(first_heading(plan_text) or fallback_title),
        "STAMP": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "SOURCE": html.escape(source_label),
        "BODYCLASS": "has-toc" if toc else "",
        "TOC": toc,
        "BODY": body,
        "SCRIPT": PAGE_SCRIPT.replace("__CONFIG__", json.dumps(page_config(body))),
    }
    # Single pass, so substituted content is never re-scanned for placeholders.
    return re.sub(r"__([A-Z]+)__", lambda m: values[m.group(1)], TEMPLATE)


# --------------------------------------------------------------------------
# Hook entry point
# --------------------------------------------------------------------------

def main():
    raw = sys.stdin.buffer.read()  # bytes: avoid the console code page mangling UTF-8
    payload = json.loads(raw.decode("utf-8", errors="replace")) if raw.strip() else {}
    tool_input = payload.get("tool_input") or {}

    plan_path = tool_input.get("planFilePath")
    plan_text = None
    if plan_path and Path(plan_path).is_file():
        plan_text = Path(plan_path).read_text(encoding="utf-8", errors="replace")
    if not plan_text:
        plan_text = tool_input.get("plan")
    if not plan_text:
        return

    if REQUIRE_SUMMARY and not has_summary(plan_text):
        # Deny the tool call; Claude sees the reason, adds the section and retries.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": SUMMARY_REASON,
        }}))
        return

    if plan_path:
        out_path = Path(plan_path).with_suffix(".html")
    else:
        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
        out_path = project_dir / "plans" / f"plan-{datetime.now():%Y%m%d-%H%M%S}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)

    page = build_page(plan_text, plan_path or "ExitPlanMode tool input", out_path.stem)
    out_path.write_text(page, encoding="utf-8")

    if OPEN_IN_BROWSER and not os.environ.get("PLAN_TO_HTML_NO_BROWSER"):
        import webbrowser
        webbrowser.open(out_path.resolve().as_uri())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # report, but never block the plan
        print(f"plan_to_html hook failed: {exc}", file=sys.stderr)
    sys.exit(0)
