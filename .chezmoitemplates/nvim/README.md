# Neovim config (for VS Code via `vscode-neovim`)

This config is built for the [`asvetliakov.vscode-neovim`](https://github.com/vscode-neovim/vscode-neovim)
extension. Inside VS Code, Neovim handles **motions, editing, text objects,
registers, and macros**; VS Code handles **everything else** (UI, LSP,
completion, file tree, search, terminal, scrolling, line numbers). Anything
VS Code-specific is gated behind `vim.g.vscode`, so the config still works if you
ever launch standalone Neovim.

## Layout

```
init.lua                  leader + bootstrap
lua/config/options.lua    options (display opts only apply to standalone nvim)
lua/config/keymaps.lua    keymaps (universal + a vim.g.vscode branch)
lua/config/lazy.lua       lazy.nvim bootstrap
lua/plugins/*.lua         plugin specs (flash, nvim-surround, targets.vim)
```

## Plugins

Picked to be vscode-neovim-safe (they operate on buffer text, not the UI):

- **flash.nvim** — `s` to jump anywhere on screen.
- **nvim-surround** — `ys`/`cs`/`ds` to add/change/delete surrounding pairs.
- **targets.vim** — richer text objects (`ci,`, `din(`, seeking `I`/`A`, ...).

On first launch lazy.nvim clones itself and installs these. Manage them with
`:Lazy`.

## Keymaps

Leader is `<space>`.

### Universal (VS Code + standalone)

| Key | Action |
| --- | --- |
| `<Esc>` (normal) | clear search highlight |
| `<` / `>` (visual) | indent, keep selection |
| `<leader>p` (visual) | paste over selection without losing the register |
| `<leader>d` | delete to black-hole register |
| `<leader>y` / `<leader>Y` | yank to system clipboard |
| `J` | join lines, keep cursor put |
| `s` | flash jump (plugin) |

### VS Code only — code navigation

| Key | Action |
| --- | --- |
| `gd` / `gD` | go to definition / declaration |
| `gr` / `gi` / `gy` | references / implementation / type definition |
| `K` | hover |
| `[d` / `]d` | previous / next diagnostic |
| `<leader>cr` | rename symbol |
| `<leader>ca` | code action / quick fix |
| `<leader>cf` | format document (or selection in visual) |
| `<leader>cp` | peek definition |
| `<leader>cR` | refactor menu |
| `<leader>cs` | source action (organize imports, ...) |
| `gcc` / `gc` (visual) | toggle comment (language-aware) |

### VS Code only — files, windows, terminal

| Key | Action |
| --- | --- |
| `<leader><leader>` / `<leader>ff` | quick open file |
| `<leader>fg` | find in files |
| `<leader>fs` | go to symbol in file |
| `<leader>fc` | command palette |
| `<leader>fr` | recent files |
| `<leader>w` | save |
| `<leader>e` | toggle sidebar |
| `<leader>xx` | problems panel |
| `]c` / `[c` | next / previous git change |
| `<leader>gg` | source control view |
| `<S-h>` / `<S-l>` | previous / next editor tab |
| `<leader>bd` | close editor |
| `<C-h/j/k/l>` | focus editor group left/down/up/right |
| `<leader>sv` / `<leader>sh` | split right / down |
| `<leader>sx` | close split |
| `<leader>tt` | toggle terminal |

## Notes / gotchas

- **`<S-h>` / `<S-l>`** shadow the default H/L (top/bottom of viewport). Switch
  them to `[b` / `]b` in `keymaps.lua` if you'd rather keep H/L.
- **System clipboard:** by default `y`/`p` use Neovim registers; `<leader>y`
  reaches the system clipboard. To make `y`/`p` always use the system clipboard,
  uncomment `opt.clipboard = "unnamedplus"` in `options.lua`.
- **Adding more VS Code commands:** find a command's id via the Command Palette
  (gear icon → "Copy Command ID") and bind it with
  `vim.keymap.set("n", "<lhs>", function() require("vscode").action("the.command.id") end)`.
  Use `require("vscode").call(...)` instead if you need it to run synchronously.
- **`vscode-neovim` Lua API:** `require("vscode")` (the old `vscode-neovim`
  module name is deprecated).
