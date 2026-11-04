#!/usr/bin/env python3
"""
Claude Code hook: PreToolUse, matcher "ExitPlanMode".

Fires when Claude finishes a plan and asks for approval. Writes an HTML copy
of the plan next to the plan's .md file (e.g. plans/foo.md -> plans/foo.html)
so it can be reviewed in a browser before approving.

Never blocks plan approval: always exits 0.
Optional: `pip install markdown` for proper rendering; without it the plan is
embedded as preformatted text.
"""
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path

OPEN_IN_BROWSER = True # set True to pop the plan open automatically

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root { --fg:#1f2328; --bg:#ffffff; --muted:#59636e; --code:#f6f8fa; --border:#d1d9e0; }
  @media (prefers-color-scheme: dark) {
    :root { color-scheme: dark; --fg:#e6edf3; --bg:#0d1117; --muted:#9198a1; --code:#161b22; --border:#3d444d; }
  }
  body { font-family: system-ui, sans-serif; color: var(--fg); background: var(--bg);
         max-width: 860px; margin: 2rem auto; padding: 0 1rem; line-height: 1.55; }
  h1, h2, h3 { border-bottom: 1px solid var(--border); padding-bottom: .3em; }
  code, pre { font-family: Consolas, "Cascadia Code", monospace; background: var(--code); }
  code { padding: .1em .3em; border-radius: 4px; }
  pre { padding: 1em; overflow-x: auto; border-radius: 6px; border: 1px solid var(--border); }
  pre code { padding: 0; background: none; }
  table { border-collapse: collapse; }
  th, td { border: 1px solid var(--border); padding: .4em .7em; }
  .meta { color: var(--muted); font-size: .85em; }
</style>
</head>
<body>
<p class="meta">Generated __STAMP__ from __SOURCE__</p>
__BODY__
</body>
</html>
"""


def render(markdown_text: str) -> str:
    try:
        import markdown  # pip install markdown
        return markdown.markdown(
            markdown_text, extensions=["fenced_code", "tables", "sane_lists"]
        )
    except ImportError:
        return f"<pre>{html.escape(markdown_text)}</pre>"


def main() -> None:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input") or {}

    plan_path = tool_input.get("planFilePath")
    plan_text = tool_input.get("plan")

    if not plan_text and plan_path and Path(plan_path).is_file():
        plan_text = Path(plan_path).read_text(encoding="utf-8")
    if not plan_text:
        return

    if plan_path:
        out_path = Path(plan_path).with_suffix(".html")
    else:
        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
        out_dir = project_dir / "plans"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"plan-{datetime.now():%Y%m%d-%H%M%S}.html"

    page = (
        TEMPLATE.replace("__TITLE__", html.escape(out_path.stem))
        .replace("__STAMP__", datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("__SOURCE__", html.escape(plan_path or "ExitPlanMode tool input"))
        .replace("__BODY__", render(plan_text))
    )
    out_path.write_text(page, encoding="utf-8")

    if OPEN_IN_BROWSER:
        import webbrowser
        webbrowser.open(out_path.resolve().as_uri())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # report, but never block the plan
        print(f"plan_to_html hook failed: {exc}", file=sys.stderr)
    sys.exit(0)
