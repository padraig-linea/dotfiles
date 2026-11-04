# Configuration inventory

A complete reference of every configuration this repo manages — whether chezmoi applies it
automatically, a `run_once_`/`run_onchange_` script automates it, or it's deliberately manual —
plus a fully detailed, standalone procedure for reinstalling the CaskaydiaCove Nerd Font by
hand. This document is source-only (see `.chezmoiignore`); it's not deployed to `$HOME`.

Written to be followable on its own, without assuming the reader has read `README.md` first —
some things are repeated from there for that reason.

## 1. Configurations chezmoi applies directly (no script involved)

| Source | Deployed to | Notes |
|---|---|---|
| `dot_bashrc`, `dot_bash_profile` | `~/.bashrc`, `~/.bash_profile` | Git Bash shell config. Fully portable, no OS branching. |
| `dot_gitconfig` | `~/.gitconfig` | Global git identity (`user.name`, `user.email`). Plain text, no secrets, portable as-is. |
| `dot_ssh/config` | `~/.ssh/config` | SSH client host aliases/settings — **never** keys or secrets. Started empty (with a comment-only template) on 2026-07-13; add host entries as you create them, then `chezmoi add ~/.ssh/config` + commit to capture them. |
| `dot_minttyrc` | `~/.minttyrc` | mintty (Git Bash's bundled terminal) font config: `Font=CaskaydiaCove NFM`. Windows/Git-Bash-only — excluded on Linux via `.chezmoiignore`. This is *already* automated; see §4 for why the font install itself isn't covered by this one file. |
| `dot_vscode/extensions.txt` | `~/.vscode/extensions.txt` | List of VS Code extension IDs (`code --list-extensions` output). Portable, no branching. |
| `winget-packages.json` | `~/winget-packages.json` | `winget export` output — Windows-installed software list. Windows-only; excluded on Linux. |
| `.chezmoitemplates/vscode-settings.json` + its two `.tmpl` wrappers | `~/.config/Code/User/settings.json` (Linux) or `~/AppData/Roaming/Code/User/settings.json` (Windows) | VS Code user settings. Templated because the two OSes disagree on the path — see `README.md`'s "why some files exist twice". |
| `.chezmoitemplates/nvim/` (10 files) + its 20 `.tmpl` wrappers | `~/.config/nvim/...` (Linux) or `~/AppData/Local/nvim/...` (Windows) | Neovim config, built to back the `asvetliakov/vscode-neovim` VS Code extension. Same templating reason as VS Code settings. |
| `dot_claude/settings.json` | `~/.claude/settings.json` | Claude Code global settings (model, effort level, TUI mode, theme, editor mode). `statusLine.command` runs `npx -y ccstatusline@latest`, styled by the file below. `~/.claude/` is Claude Code's own convention on every OS — unlike VS Code/Neovim it doesn't split by Windows-AppData vs. Linux-XDG, so no templating is needed here. |
| `dot_config/ccstatusline/settings.json` | `~/.config/ccstatusline/settings.json` | ccstatusline's own config (line/segment layout, colors, powerline theme). ccstatusline is an npm CLI tool that always resolves to `~/.config/ccstatusline` regardless of OS (no XDG/AppData split), so no templating needed. The tool itself isn't installed persistently — `npx -y ccstatusline@latest` fetches/caches it on each run; only the Node.js runtime it needs is tracked (via `winget-packages.json`, `OpenJS.NodeJS.LTS`). To reconfigure by hand (change segments/colors/layout), run `npx ccstatusline@latest` directly in a terminal — it launches an interactive TUI configurator and overwrites this file; re-run `chezmoi add ~/.config/ccstatusline/settings.json` afterwards to pull the change back into this repo. Caveat: `npx` always fetches the latest ccstatusline, unpinned, so a future version could in principle change its settings schema in a way an old tracked file doesn't match — if that happens, just re-run the configurator to regenerate it. |
| `dot_claude/statusline-command.sh` | `~/.claude/statusline-command.sh` | Superseded by ccstatusline above (`settings.json` no longer references it) — kept tracked as a portable-bash fallback statusline (needs `jq` on `PATH`) in case ccstatusline is ever removed. Not currently invoked. |
| `dot_claude/CLAUDE.md` | `~/.claude/CLAUDE.md` | Claude Code global instructions (communication and writing-style preferences, git rules). Plain markdown, portable. |
| `dot_claude/commands/pulse.md` | `~/.claude/commands/pulse.md` | Claude Code custom slash command (`/pulse`, configures the claude-pulse status bar). Add further `~/.claude/commands/*.md` files with `chezmoi add` as you create them. |
| `dot_claude/hooks/` | `~/.claude/hooks/` | Claude Code hook scripts. `dot_claude/settings.json` calls them, so they must exist wherever that file is deployed. `notify.ps1` shows a Windows toast and plays a sound when Claude stops, needs permission, or goes idle. It runs through `powershell.exe`, so it only works on Windows. `plan_to_html.py` writes an HTML copy of each plan when Claude exits plan mode. It needs `python` on `PATH`; `pip install markdown` gives better rendering. `sounds/bell-triple.wav` is the sound `notify.ps1` plays on Stop. `sounds/make-bells.js` regenerates it, plus four other bells, with `node make-bells.js <output-dir>`. `.chezmoiignore` excludes `__pycache__`. |
| `dot_config/git/ignore` | `~/.config/git/ignore` | Global gitignore — git's default `core.excludesFile` location on every OS, so no `.gitconfig` entry is needed to point at it. |
| `AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json` | `~/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json` | Windows Terminal settings: profiles, fonts, keybindings, colour scheme, default profile. Windows-only; excluded on Linux. Tracked verbatim — the Git Bash profile is a static, user-defined entry with a fixed GUID, and Windows Terminal generates its built-in/dynamic profile GUIDs deterministically, so the whole file ports between machines. Windows Terminal rewrites this file whenever you change a setting in its UI; run `chezmoi re-add` on it afterwards to capture the change. The Git Bash profile's `startingDirectory` is `C:\Projects\Onion` — edit it if a machine doesn't have that path. Only valid for the Store/MSIX install of Windows Terminal; an unpackaged install keeps its settings elsewhere. |

## 2. Configurations applied via automation scripts

chezmoi scripts run as part of `chezmoi apply`. `run_onchange_` scripts re-run whenever the
content they're keyed to changes; `run_once_` scripts run once and only re-run if edited or if
the previous run failed.

| Script | Type | What it does |
|---|---|---|
| `run_onchange_after_nvim-lazy-sync.{sh,ps1}.tmpl` | onchange, OS-gated | Runs `nvim --headless "+Lazy! restore" +qa` to (re)install lazy.nvim's plugins at the versions pinned in `lazy-lock.json`. Re-triggers whenever that file's content changes. |
| `run_onchange_after_vscode-extensions-sync.{sh,ps1}.tmpl` | onchange, OS-gated | Installs every extension listed in `dot_vscode/extensions.txt` via `code --install-extension`. Re-triggers whenever that file's content changes. |
| `run_once_after_install-nerd-font.ps1.tmpl` | once, Windows-only | Downloads and installs the CaskaydiaCove Nerd Font at user scope (see §4 for exactly what this does — it's the scripted version of that same procedure). Skips itself if the font already appears installed. |

Windows Terminal's Git Bash profile font used to be set by a separate `run_once_` script.
That script was removed on 2026-11-03 when `settings.json` itself became tracked (§1): a script
editing a chezmoi-managed file would be reverted on the next `chezmoi apply`.

## 3. Deliberately NOT tracked or automated at all

| What | Why |
|---|---|
| SSH keys (`~/.ssh/`) | Secrets. Copy them to a new machine yourself, over a secure channel, never through this repo. |
| Neovim plugin data (`nvim-data`) | Just downloaded plugin code, rebuilt automatically from `lazy-lock.json` (§2) — committing it would be dead weight. |
| VS Code caches/session state (`globalStorage`, `History`, `workspaceStorage`, etc.) | Internal state, not real config. |
| Actually **installing** winget packages | `winget-packages.json` is tracked as data (§1), but running `winget import` is left manual — it installs ~38 arbitrary packages, some large/interactive (Office, Teams), which isn't appropriate for an unattended background script. Restore with: `winget import -i winget-packages.json --ignore-unavailable`. |
| `~/.claude/skills/` | Contains only `synced/` (skills pushed from the claude.ai organisation, stored under opaque bucket IDs) and `.trash/`. Both are managed by Claude Code itself and re-synced on a new machine after login. If you ever write a skill by hand, `chezmoi add` that one directory. |
| `~/.claude/.credentials.json` | OAuth/auth credentials — a secret, same category as SSH keys. Never tracked. |
| `~/.claude/history.jsonl`, session transcripts under `~/.claude/projects/<project>/*.jsonl` | Internal formats that change between Claude Code versions — not meant to be parsed/moved directly, and not real "configuration." Use Claude Code's own `/export` command to save a specific session as a readable file if you want to keep/move one. |
| `~/.claude.json` | Global app state, including OAuth session tokens and per-project trust decisions. Tokens are machine/session-specific and won't work if copied to a new machine — re-authenticate there instead (`claude auth login` or equivalent). |
| `~/.claude/remote-settings.json` | Org-managed policy (plugin marketplace allow/block-lists) — pushed by an employer/admin, not something configured by hand. Doesn't belong in a personal dotfiles repo, and would be actively wrong to carry over to a different organization's machine. || `~/.claude/{cache,backups,file-history,ide,paste-cache,plans,plugins,projects,session-env,sessions,shell-snapshots}/`, `.last-cleanup`, `mcp-needs-auth-cache.json`, `policy-limits.json`, `projects-backup-*.zip`, `settings-backup-*.json` | Runtime/cache/session state and automatic backups, all regenerated by Claude Code itself — same category as `nvim-data` and VS Code's caches. The one exception is `~/.claude/projects/<project>/memory/*.md` (the auto-memory system) — plain markdown, genuinely portable, but left as a manual copy rather than tracked here since it's Claude-authored working data, not something you'd hand-edit. **`export-claude-memory.sh`** (tracked in this repo, excluded from deployment like this file) automates collecting every project's memory `*.md` files into one bundle: run `bash export-claude-memory.sh [output-dir]` on the old machine, transfer the resulting folder over any secure channel (not through this repo), then on the new machine open each project in Claude Code once first (so it creates that project's correctly-sanitized directory for its new path) and copy the matching bundle folder's `*.md` files into that project's fresh `memory/` directory. The script can't compute the new machine's directory names itself — sanitized project-path names differ per machine, especially across OSes — so that last step stays manual; its own output `MANIFEST.md` repeats these instructions. |

## 4. Manual procedure: reinstalling the CaskaydiaCove Nerd Font

The `install-nerd-font` script in §2 automates §4.1 below. This section exists as a complete,
standalone fallback — for a machine where you'd rather not run the scripts, for manually
verifying what they do, or for recovering if one of them fails partway through. Every step is
a literal, copy-pasteable PowerShell command; nothing here assumes prior context beyond having
a Windows machine with PowerShell available.

### 4.1 Install the font files (user scope, no admin required)

```powershell
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$tmp = "$env:TEMP\nerdfont"
New-Item -ItemType Directory -Force $tmp | Out-Null
$zip = "$tmp\CascadiaCode.zip"
$ext = "$tmp\CascadiaCode"

# Download the official Nerd Fonts release for Cascadia Code
Invoke-WebRequest -Uri 'https://github.com/ryanoasis/nerd-fonts/releases/latest/download/CascadiaCode.zip' -OutFile $zip
Expand-Archive -Path $zip -DestinationPath $ext -Force

# Install every .ttf for the current user and register each in HKCU
$fontsDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force $fontsDir | Out-Null
$regPath = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
Add-Type @"
using System; using System.Runtime.InteropServices;
public class NativeFonts { [DllImport("gdi32.dll")] public static extern int AddFontResource(string p); }
"@
foreach ($f in Get-ChildItem $ext -Recurse -Filter '*.ttf') {
    $dest = Join-Path $fontsDir $f.Name
    Copy-Item $f.FullName $dest -Force
    [void][NativeFonts]::AddFontResource($dest)
    New-ItemProperty -Path $regPath -Name "$($f.BaseName) (TrueType)" -Value $dest -PropertyType String -Force | Out-Null
}
```

**Gotcha:** do **not** broadcast `WM_FONTCHANGE` synchronously to `HWND_BROADCAST` as a way to
make running apps notice the new font immediately — it can hang indefinitely if any open
window is unresponsive (this happened during the original setup). Just restart the apps that
need to see it (see §4.4) instead of trying to force a live refresh.

**To verify it worked:**
```powershell
Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Fonts" -Filter 'Caskaydia*' | Select-Object Name
```
This should list ~36 font files. The specific family name used everywhere in this repo is the
abbreviated **`CaskaydiaCove NFM`** (the "Mono" variant) — not "CaskaydiaCove Nerd Font Mono".

### 4.2 Windows Terminal's Git Bash profile font

Windows Terminal's `settings.json` is tracked whole (§1), so the Git Bash profile's font comes
from this repo, not from a script. It is currently `Cascadia Code`. Recent releases of Cascadia
Code (2404.23 and later, as bundled with current Windows Terminal) include the Nerd Font symbol
set, so icons render with it. To use the font installed in §4.1 instead, change that profile's
`font.face` to `CaskaydiaCove NFM` in the tracked `settings.json`, then run `chezmoi apply`.

### 4.3 mintty's font (direct Git Bash launches, not via Windows Terminal)

Already handled — `dot_minttyrc` (tracked by chezmoi, §1) deploys `~/.minttyrc` containing:
```ini
Font=CaskaydiaCove NFM
FontHeight=11
```
No manual action needed here as long as chezmoi has been applied at least once.

### 4.4 See it take effect

**Fully close and reopen Windows Terminal** (all windows, not just the tab). Icons next to
filenames (from `eza`) only render once the terminal is actually using a Nerd Font — if you
see boxes/▯ instead of icons, the font hasn't taken effect yet, usually because the terminal
wasn't fully restarted.

**Optional — VS Code's integrated terminal** is not covered by any of the above (it's a
separate font setting from Windows Terminal/mintty). To get icons there too, add to VS Code's
`settings.json`:
```json
"terminal.integrated.fontFamily": "CaskaydiaCove NFM"
```
