# Automatically starting the SSH agent
env=~/.ssh/agent.env

agent_load_env () { test -f "$env" && . "$env" >| /dev/null ; }

agent_start () {
    (umask 077; ssh-agent >| "$env")
    . "$env" >| /dev/null ; }

agent_load_env

# agent_run_state: 0=agent running w/ key; 1=agent w/o key; 2=agent not running
agent_run_state=$(ssh-add -l >| /dev/null 2>&1; echo $?)

if [ ! "$SSH_AUTH_SOCK" ] || [ $agent_run_state = 2 ]; then
    agent_start
    ssh-add ~/.ssh/id_ed25519
elif [ "$SSH_AUTH_SOCK" ] && [ $agent_run_state = 1 ]; then
    ssh-add ~/.ssh/id_ed25519
fi

unset env



# Added by Patrick

# Git related
alias gap="git apply"
alias glo="git log --oneline"
alias glg="git log"
alias glo9="git log --oneline -9"
alias glf="git log --pretty=full -9"
alias gst="git status"
alias gau="git add -u"
alias gbr="git branch"
alias gco="git checkout"
alias gdf="git difftool"
alias gdfs="git diff --staged"
alias gdfno="git diff --name-only"
alias gfat="git fetch --all --tags"
alias gcs="git commit -s"
alias gca="git commit --amend"
alias gad="git add"
alias gaa="git add -A"
alias gpt="git push --tags"
alias grc="git rebase --continue"
alias gsh="git stash"
alias gsp="git stash pop"
alias gsl="git stash list"
alias gfo="git fetch origin"
alias gtg="git tag"
alias grs="git restore --staged"

# Dotfiles (bare repo tracking $HOME directly — the "bare-repo trick")
# NOTE: deliberately an alias with explicit flags, not exported GIT_DIR/GIT_WORK_TREE —
# exporting those would hijack every other git command run in this shell.
alias dotfiles='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'


# Added by Claude — navigation, listing & conveniences (2026-06-24)

# --- Listing (uses eza when available, falls back to ls) ---
alias grep='grep --color=auto'
if command -v eza >/dev/null 2>&1; then
    alias ls='eza --icons=auto --group-directories-first --color=auto'
    alias l='eza --icons=auto --group-directories-first --color=auto'
    alias la='eza -a --icons=auto --group-directories-first --color=auto'          # all, incl. dotfiles
    alias ll='eza -l --git --icons=auto --group-directories-first --color=auto'    # long + git status
    alias lla='eza -la --git --icons=auto --group-directories-first --color=auto'  # long + all + git
    alias lt='eza -l --sort=modified --icons=auto --group-directories-first --color=auto'  # by mtime
    # file-type icons need a Nerd Font in your terminal (CaskaydiaCove NFM installed)
else
    alias ls='ls --color=auto'   # colorize ls output
    alias l='ls -CF'             # compact columns, classify (*/=@|)
    alias la='ls -a'             # list all, including dotfiles
    alias ll='ls -lh'            # long form, human-readable sizes
    alias lla='ls -lha'          # long form, all files, human-readable
    alias lt='ls -lhtr'          # long form sorted by mtime (newest last)
fi

# --- Navigation ---
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
# make a directory (and parents) then cd into it:  mkcd path/to/new/dir
mkcd() { mkdir -p "$1" && cd "$1"; }

# --- Conveniences ---
alias cls='clear'
alias reload='source ~/.bashrc'              # re-read this file after edits
alias h='history'
alias path='echo "$PATH" | tr ":" "\n"'      # print PATH one entry per line
alias df='df -h'
alias du='du -h'

# --- File tree ---
# tree [dir] [-L depth]   colored, git-aware tree via eza (falls back to Windows tree.com)
if command -v eza >/dev/null 2>&1; then
    tree() { eza --tree --icons=auto --color=auto "$@"; }
else
    # native fallback only takes an optional dir; scan args for the first non-flag
    # token (skipping -L/--level and its numeric value) regardless of position
    tree() {
        local d="." found=0
        while [ $# -gt 0 ]; do
            case "$1" in
                -L|--level) if [ $# -ge 2 ]; then shift 2; else shift; fi ;;
                -*) shift ;;
                *) [ "$found" -eq 0 ] && d="$1"; found=1; shift ;;
            esac
        done
        ( cd "$d" && cmd //c "tree /F /A"; )
    }
fi
# ftree [dir] [depth]   pure-bash fallback with depth limit (default depth 2)
ftree() { find "${1:-.}" -maxdepth "${2:-2}" 2>/dev/null \
            | sed -e 's;[^/]*/;|__;g;s;__|; |;g'; }
