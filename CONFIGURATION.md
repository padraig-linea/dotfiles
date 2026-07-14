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
| `dot_claude/settings.json` | `~/.claude/settings.json` | Claude Code global settings (model, effort level, TUI mode, theme, editor mode). `statusLine.command` runs `npx -y ccstatusline@latest` — see §3 for why ccstatusline's own config isn't tracked here too. `~/.claude/` is Claude Code's own convention on every OS — unlike VS Code/Neovim it doesn't split by Windows-AppData vs. Linux-XDG, so no templating is needed here. |
| `dot_claude/statusline-command.sh` | `~/.claude/statusline-command.sh` | Superseded by ccstatusline above (`settings.json` no longer references it) — kept tracked as a portable-bash fallback statusline (needs `jq` on `PATH`) in case ccstatusline is ever removed. Not currently invoked. |

## 2. Configurations applied via automation scripts

chezmoi scripts run as part of `chezmoi apply`. `run_onchange_` scripts re-run whenever the
content they're keyed to changes; `run_once_` scripts run once and only re-run if edited or if
the previous run failed.

| Script | Type | What it does |
|---|---|---|
| `run_onchange_after_nvim-lazy-sync.{sh,ps1}.tmpl` | onchange, OS-gated | Runs `nvim --headless "+Lazy! restore" +qa` to (re)install lazy.nvim's plugins at the versions pinned in `lazy-lock.json`. Re-triggers whenever that file's content changes. |
| `run_onchange_after_vscode-extensions-sync.{sh,ps1}.tmpl` | onchange, OS-gated | Installs every extension listed in `dot_vscode/extensions.txt` via `code --install-extension`. Re-triggers whenever that file's content changes. |
| `run_once_after_install-nerd-font.ps1.tmpl` | once, Windows-only | Downloads and installs the CaskaydiaCove Nerd Font at user scope (see §4 for exactly what this does — it's the scripted version of that same procedure). Skips itself if the font already appears installed. |
| `run_once_after_set-gitbash-terminal-font.ps1.tmpl` | once, Windows-only | Finds the Git Bash profile in Windows Terminal's `settings.json` (by name/commandline, since its GUID differs per machine) and sets its `font.face` to `CaskaydiaCove NFM`. Only touches that one field on that one profile. Backs up `settings.json` first. Fails loudly (and gets automatically retried on the next apply) if no Git Bash profile exists yet — e.g. on a machine where Windows Terminal hasn't been opened once yet to auto-detect Git for Windows. |

Execution order between the two font scripts matters (font must exist before a profile can
usefully reference it) — both are named so alphabetical script ordering runs
`install-nerd-font` before `set-gitbash-terminal-font` without needing explicit `before_`/`after_`
attributes.

## 3. Deliberately NOT tracked or automated at all

| What | Why |
|---|---|
| SSH keys (`~/.ssh/`) | Secrets. Copy them to a new machine yourself, over a secure channel, never through this repo. |
| Neovim plugin data (`nvim-data`) | Just downloaded plugin code, rebuilt automatically from `lazy-lock.json` (§2) — committing it would be dead weight. |
| VS Code caches/session state (`globalStorage`, `History`, `workspaceStorage`, etc.) | Internal state, not real config. |
| Actually **installing** winget packages | `winget-packages.json` is tracked as data (§1), but running `winget import` is left manual — it installs ~38 arbitrary packages, some large/interactive (Office, Teams), which isn't appropriate for an unattended background script. Restore with: `winget import -i winget-packages.json --ignore-unavailable`. |
| Windows Terminal's `settings.json` as a whole | Only the Git Bash profile's font field is touched (§2), surgically, by script. The rest of the file is never tracked or overwritten — profile GUIDs and other settings differ per machine, so deploying the whole file would risk clobbering things a given machine already has. |
| `~/.claude/.credentials.json` | OAuth/auth credentials — a secret, same category as SSH keys. Never tracked. |
| `~/.claude/history.jsonl`, session transcripts under `~/.claude/projects/<project>/*.jsonl` | Internal formats that change between Claude Code versions — not meant to be parsed/moved directly, and not real "configuration." Use Claude Code's own `/export` command to save a specific session as a readable file if you want to keep/move one. |
| `~/.claude.json` | Global app state, including OAuth session tokens and per-project trust decisions. Tokens are machine/session-specific and won't work if copied to a new machine — re-authenticate there instead (`claude auth login` or equivalent). |
| `~/.claude/remote-settings.json` | Org-managed policy (plugin marketplace allow/block-lists) — pushed by an employer/admin, not something configured by hand. Doesn't belong in a personal dotfiles repo, and would be actively wrong to carry over to a different organization's machine. |
| `~/.config/ccstatusline/settings.json` | ccstatusline (the statusline styler `dot_claude/settings.json` invokes via `npx -y ccstatusline@latest`, §1) writes its own layout/segment/color config here. Not tracked — after installing (i.e. once Node.js is present, via `winget-packages.json`), run `npx ccstatusline@latest` directly in a terminal to launch its interactive TUI configurator and (re)generate this file to taste, rather than syncing one machine's generated preferences to another. |
| `~/.claude/{cache,backups,file-history,ide,paste-cache,plans,plugins,projects,session-env,sessions,shell-snapshots}/`, `.last-cleanup`, `mcp-needs-auth-cache.json`, `policy-limits.json`, `projects-backup-*.zip`, `settings-backup-*.json` | Runtime/cache/session state and automatic backups, all regenerated by Claude Code itself — same category as `nvim-data` and VS Code's caches. The one exception is `~/.claude/projects/<project>/memory/*.md` (the auto-memory system) — plain markdown, genuinely portable, but left as a manual copy rather than tracked here since it's Claude-authored working data, not something you'd hand-edit. **`export-claude-memory.sh`** (tracked in this repo, excluded from deployment like this file) automates collecting every project's memory `*.md` files into one bundle: run `bash export-claude-memory.sh [output-dir]` on the old machine, transfer the resulting folder over any secure channel (not through this repo), then on the new machine open each project in Claude Code once first (so it creates that project's correctly-sanitized directory for its new path) and copy the matching bundle folder's `*.md` files into that project's fresh `memory/` directory. The script can't compute the new machine's directory names itself — sanitized project-path names differ per machine, especially across OSes — so that last step stays manual; its own output `MANIFEST.md` repeats these instructions. |

## 4. Manual procedure: reinstalling the CaskaydiaCove Nerd Font

The two scripts in §2 automate everything below. This section exists as a complete,
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

### 4.2 Point Windows Terminal's Git Bash profile at the font

Windows Terminal profile GUIDs are machine-specific (they're generated per-machine when
Windows Terminal auto-detects Git for Windows), so the profile must be found by name/commandline
rather than by a fixed GUID:

```powershell
$wt = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"

# Back up first
$backup = "$wt.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $wt $backup

$json = Get-Content $wt -Raw | ConvertFrom-Json
$gitBash = $json.profiles.list | Where-Object {
    $_.name -like '*Git Bash*' -or $_.commandline -like '*git-bash*' -or $_.commandline -like '*bash.exe*'
} | Select-Object -First 1

if (-not $gitBash) {
    Write-Warning "No Git Bash profile found. Open Windows Terminal at least once (it auto-detects Git for Windows and creates the profile), then re-run this block."
} else {
    $fontObj = [PSCustomObject]@{ face = 'CaskaydiaCove NFM' }
    $gitBash | Add-Member -MemberType NoteProperty -Name font -Value $fontObj -Force
    $out = $json | ConvertTo-Json -Depth 32
    [System.IO.File]::WriteAllText($wt, $out, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "Set font on profile: $($gitBash.name)"
}
```

If Windows Terminal hasn't been opened yet on this machine, there won't be a Git Bash profile
to find — open it once first, then re-run the block above.

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
