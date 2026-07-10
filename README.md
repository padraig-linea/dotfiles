# dotfiles

Personal config for Git Bash + Neovim + VS Code, managed with [chezmoi](https://www.chezmoi.io/)
so it can be restored on a new machine — Windows or Linux — without redoing everything by hand.

> **History note (2026-07-10):** this repo used to be managed via the git "bare-repo trick"
> (a bare repo at `~/.dotfiles` with `--work-tree=$HOME`, tracking real files in place). That
> approach couldn't express "same config, different path per OS" (Neovim wants
> `~/AppData/Local/nvim` on Windows but `~/.config/nvim` on Linux), so it was migrated to
> chezmoi. `~/.dotfiles` still exists on the original machine but is retired — don't run any
> `dotfiles` commands against it again.

This file itself is source-only documentation — it's excluded from deployment (see
`.chezmoiignore`), so it won't clutter `~/README.md` on machines this gets applied to.

## The confusing part, explained simply

chezmoi doesn't track your real files directly. Instead, this repo (the "source state") holds
a *managed representation* of each file, and `chezmoi apply` renders/copies that into its real
location under `$HOME`. A few naming rules control where each file ends up:
- a `dot_` prefix on a name becomes a leading dot: `dot_bashrc` → `~/.bashrc`
- a `.tmpl` suffix means the file's *content* is a template, evaluated at apply time
- each path segment is handled independently: `dot_config/nvim/init.lua` → `~/.config/nvim/init.lua`

Practically, this means `chezmoi apply` is a one-way copy from this repo into `$HOME`, not a
symlink — edit the source (or run `chezmoi add <file>` after editing the real file), then
`chezmoi apply` to push it back out.

## The other confusing part: why some files exist twice

chezmoi has no way to say "put this same content at a different absolute path depending on the
OS" (it's a known, currently unimplemented gap — see
[chezmoi issue #2273](https://github.com/twpayne/chezmoi/issues/2273)). Neovim and VS Code
both need genuinely different target paths on Windows vs. Linux, so those configs use this
pattern instead:
- the real content lives once, under `.chezmoitemplates/` (e.g. `.chezmoitemplates/nvim/init.lua`)
- a thin one-line wrapper file exists at **both** possible target paths — e.g.
  `dot_config/nvim/init.lua.tmpl` **and** `AppData/Local/nvim/init.lua.tmpl` — each containing
  just `{{- template "nvim/init.lua" . -}}`
- `.chezmoiignore` excludes whichever one of the pair doesn't match the current machine's OS,
  via `{{ if eq .chezmoi.os "windows" }}...{{ end }}`

So: **to edit Neovim or VS Code config, always edit the file under `.chezmoitemplates/`**, never
the wrapper files under `dot_config/` or `AppData/` — those are just plumbing.

## What's tracked here

- `dot_bashrc`, `dot_bash_profile` — Git Bash shell config (fully portable, no OS branching needed)
- `dot_minttyrc` — mintty font config. Windows/Git-Bash-only; excluded on Linux via `.chezmoiignore`
- `dot_vscode/extensions.txt` — list of installed VS Code extension IDs (portable, no branching)
- `winget-packages.json` — list of winget-installed software (like `pip freeze`, but for
  winget). Windows-only concept; excluded on Linux via `.chezmoiignore`
- `.chezmoitemplates/vscode-settings.json` + its two `.tmpl` wrappers — VS Code user settings
- `.chezmoitemplates/nvim/` (10 files) + its 20 `.tmpl` wrappers — Neovim config, built
  specifically to back the `asvetliakov/vscode-neovim` VS Code extension

## What's deliberately NOT tracked

- **SSH keys** (`~/.ssh/`) — these are secrets. Copy them to a new machine yourself, over a
  secure channel, separately from this repo.
- **Neovim plugin data** (`nvim-data`) — this is just downloaded plugin code. It's rebuilt
  automatically from `lazy-lock.json` via a `run_onchange_after_` script (see below), so
  committing it would be dead weight.
- **VS Code caches/session data** (`globalStorage`, `History`, `workspaceStorage`, etc.) —
  internal state, not real config.

## Setting up on a brand new machine

**1. Install chezmoi:**
- Windows: `winget install twpayne.chezmoi`
- Linux: see [chezmoi's install page](https://www.chezmoi.io/install/) for your distro's
  package manager, or the one-line installer script.

**2. Get your SSH key onto the new machine first**, some other way (USB stick, secure
transfer, etc.) — needed before you can clone this repo over SSH.

**3. Initialize and apply in one step:**
```bash
chezmoi init --apply --less-interactive git@github.com:padraig-linea/dotfiles.git
```
**Always use `--less-interactive` (or `--interactive`) on a new machine, never bare
`chezmoi apply` or `--force`.** By default, `chezmoi apply` only prompts about files it
previously wrote and that changed since — for files that already exist but were never
chezmoi-managed before (exactly the new-machine case), plain `apply` silently overwrites them.
`--less-interactive` prompts before touching those too. If you want to review everything
first without changing anything, run `chezmoi diff` before `apply`.

**4. Open a new terminal window** so the new `.bashrc` (with its eza/tree aliases) and the
`chezmoi` binary's `PATH` entry both take effect.

**On Windows specifically**, step 3's apply will try to run the `.ps1` restore scripts (nvim
plugins, VS Code extensions) and may fail with `running scripts is disabled on this system` —
PowerShell's default execution policy blocks unsigned local scripts. Fix with (adjust scope to
taste; `CurrentUser` doesn't need admin):
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
then re-run `chezmoi apply --less-interactive`.

## This repo is config only — software still needs installing separately

Cloning/applying this repo brings back your *settings*, not the *programs* themselves:

- **Neovim plugins** are restored automatically — a `run_onchange_after_` script (OS-gated,
  `.sh.tmpl`/`.ps1.tmpl` pair) runs `nvim --headless "+Lazy! restore" +qa` on apply, and
  re-runs automatically whenever `lazy-lock.json`'s content changes.
- **VS Code extensions** are restored automatically the same way, from `dot_vscode/extensions.txt`.
- **winget packages** (Windows only) — reinstall manually:
  `winget import -i winget-packages.json --ignore-unavailable` (add `--ignore-version-numbers`
  to grab latest versions instead of the exact ones recorded). Regenerate this file after
  installing something new: `winget export -o winget-packages.json --accept-source-agreements`.
  Left manual deliberately — it installs ~38 arbitrary packages (some large/interactive, e.g.
  Office, Teams), not appropriate for an unattended background script.
- **CaskaydiaCove Nerd Font** + Windows Terminal's Git Bash profile font — machine-specific,
  no shortcut (see `config-migration/terminal-setup.md` on the original machine if it still
  exists).
