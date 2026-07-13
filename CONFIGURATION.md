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
| `dot_minttyrc` | `~/.minttyrc` | mintty (Git Bash's bundled terminal) font config: `Font=CaskaydiaCove NFM`. Windows/Git-Bash-only — excluded on Linux via `.chezmoiignore`. This is *already* automated; see §4 for why the font install itself isn't covered by this one file. |
| `dot_vscode/extensions.txt` | `~/.vscode/extensions.txt` | List of VS Code extension IDs (`code --list-extensions` output). Portable, no branching. |
| `winget-packages.json` | `~/winget-packages.json` | `winget export` output — Windows-installed software list. Windows-only; excluded on Linux. |
| `.chezmoitemplates/vscode-settings.json` + its two `.tmpl` wrappers | `~/.config/Code/User/settings.json` (Linux) or `~/AppData/Roaming/Code/User/settings.json` (Windows) | VS Code user settings. Templated because the two OSes disagree on the path — see `README.md`'s "why some files exist twice". |
| `.chezmoitemplates/nvim/` (10 files) + its 20 `.tmpl` wrappers | `~/.config/nvim/...` (Linux) or `~/AppData/Local/nvim/...` (Windows) | Neovim config, built to back the `asvetliakov/vscode-neovim` VS Code extension. Same templating reason as VS Code settings. |

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
