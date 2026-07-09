# dotfiles

This is my personal config for Windows + Git Bash + Neovim + VS Code, kept on GitHub so I
can get my setup back on a new machine without redoing everything by hand.

## The confusing part, explained simply

Normally, a git repo lives in its own folder — the `.git` data and the files it tracks sit
together in one place. That doesn't work well for config files, because they don't live in
one tidy folder — they're scattered all over your home folder (`~/.bashrc`,
`~/AppData/Local/nvim/...`, etc.).

So this repo does something different: the git data lives in a separate hidden folder
(`~/.dotfiles`), completely apart from the files it tracks. Your home folder (`$HOME`) is
told "these are the files this repo cares about" — but only when you use one specific
command, `dotfiles`, instead of plain `git`. Plain `git` commands anywhere else on the
machine are completely unaffected and don't even know this repo exists.

Practically, this means:
- Your real files stay exactly where they normally live — no copies, no symlinks to keep
  track of.
- Only files you've explicitly added to the repo are tracked. Everything else in your home
  folder (Downloads, other projects, caches, etc.) is invisible to it.
- You always type `dotfiles` (not `git`) to interact with it — `dotfiles status`,
  `dotfiles add`, `dotfiles commit`, `dotfiles push`.

## What's tracked here

- `.bashrc`, `.bash_profile`, `.minttyrc` — Git Bash shell config
- `AppData/Local/nvim/` — Neovim config (not the plugin data itself — see below)
- `AppData/Roaming/Code/User/settings.json` — VS Code settings
- `.vscode/extensions.txt` — list of installed VS Code extension IDs
- `winget-packages.json` — list of winget-installed software (like `pip freeze`, but for
  winget — generated with `winget export`, restored with `winget import`)

## What's deliberately NOT tracked

- **SSH keys** (`~/.ssh/`) — these are secrets. Copy them to a new machine yourself, over a
  secure channel, separately from this repo.
- **Neovim plugin data** (`nvim-data`) — this is just downloaded plugin code. It's rebuilt
  automatically from `lazy-lock.json` (see below), so committing it would be dead weight.
- **VS Code caches/session data** (`globalStorage`, `History`, `workspaceStorage`, etc.) —
  internal state, not real config.

## Setting up on a brand new machine

**1. Get your SSH key onto the new machine first**, some other way (USB stick, secure
transfer, etc.) — you need it before you can even clone this repo over SSH.

**2. Clone the repo as a "bare" repo**, into `~/.dotfiles`:
```bash
git clone --bare git@github.com:padraig-linea/dotfiles.git ~/.dotfiles
```

**3. Type the `dotfiles` shortcut command by hand, just this once.** Normally this shortcut
would already exist because it's defined inside `.bashrc` — but `.bashrc` hasn't been put in
place yet, so there's nothing to load it from. Just type this once in your current window:
```bash
alias dotfiles='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
```

**4. Tell it to ignore everything else in your home folder:**
```bash
dotfiles config --local status.showUntrackedFiles no
```

**5. Copy the actual files into place:**
```bash
dotfiles checkout
```

If this step **fails with a list of file names**, it means one of those files already
exists on the new machine (e.g. Git for Windows created its own default `.bash_profile`).
Git is refusing to overwrite something on its own — that's on purpose, so nothing gets
silently lost. For each file it lists: decide whether to keep the existing one or replace
it, rename the existing one out of the way if you want to keep it (e.g. `.bashrc.orig`),
then run `dotfiles checkout` again.

**6. Open a new terminal window** (or run `source ~/.bashrc`) so the real `dotfiles`
shortcut — now present in the `.bashrc` you just checked out — takes over from the one you
typed by hand.

## This repo is config only — software still needs installing separately

Cloning this repo brings back your *settings*, not the *programs* themselves. After step 6,
still do, separately:

- Reinstall winget software: `winget import -i winget-packages.json --ignore-unavailable`
  (add `--ignore-version-numbers` to grab latest versions instead of the exact ones
  recorded — usually what you want, since old versions can fall out of the source over
  time). Regenerate this file after installing something new with
  `winget export -o winget-packages.json --accept-source-agreements`.
- Install the CaskaydiaCove Nerd Font and set it as the Windows Terminal Git Bash profile's
  font — this part is machine-specific and has no shortcut (see the original
  `config-migration/terminal-setup.md` notes if you still have that folder around).
- Restore Neovim's plugins: `nvim --headless "+Lazy! restore" +qa`
- Restore VS Code's extensions: `cat ~/.vscode/extensions.txt | xargs -L1 code --install-extension`
