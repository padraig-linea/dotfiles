# Setup context & work log

Record of the Neovim configuration built for use with the
`asvetliakov.vscode-neovim` extension. Last updated **2026-06-23**.

## Goal & design

Neovim used **exclusively inside VS Code** via vscode-neovim. Division of labor:

- **Neovim** drives motions, editing, text objects, registers, macros, search.
- **VS Code** owns everything else: UI, LSP, completion, file tree, search,
  terminal, scrolling, scroll margin, line numbers, folding.

So the config stays lean and routes UI/LSP/file/window actions to VS Code
commands via `require("vscode").action(...)`. Everything VS Code-specific is
gated behind `vim.g.vscode`, so the config still works (and looks sane) if
standalone Neovim is ever launched.

## Files created

| File | Purpose |
| --- | --- |
| `init.lua` | Sets `<space>` leader, requires the three config modules |
| `lua/config/options.lua` | Options Neovim still controls in VS Code; display opts guarded behind `not vim.g.vscode` |
| `lua/config/keymaps.lua` | Universal maps + a `vim.g.vscode` branch routing to VS Code commands, plus a standalone `else` fallback |
| `lua/config/lazy.lua` | lazy.nvim bootstrap + plugin loading from `lua/plugins/` |
| `lua/plugins/flash.lua` | folke/flash.nvim — jump motions |
| `lua/plugins/surround.lua` | kylechui/nvim-surround — add/change/delete surrounds |
| `lua/plugins/targets.lua` | wellle/targets.vim — richer text objects |
| `README.md` | User-facing keymap reference + how to extend |
| `CONTEXT.md` | This file |

## Plugins installed (via lazy.nvim)

Chosen to be vscode-neovim-safe — they operate on buffer text, not the UI.

| Plugin | What it adds |
| --- | --- |
| `folke/flash.nvim` | `s` jump-anywhere; `r` remote (operator). `S`/`R` treesitter modes are standalone-only (no treesitter under VS Code). |
| `kylechui/nvim-surround` | `ys`/`yss`/`ds`/`cs`, visual `S` |
| `wellle/targets.vim` | `ci,`, `din(`, seeking `I`/`A`, cursor-not-inside-pair text objects |

lazy.nvim self-clones on first launch and installs these. Manage with `:Lazy`.
Confirmed installed and loading error-free on 2026-06-23.

## Options set (`lua/config/options.lua`)

Active everywhere (Neovim still controls these in VS Code):
`ignorecase`, `smartcase`, `incsearch`, `hlsearch`, `undofile`,
`timeoutlen=400`, `updatetime=250`, `expandtab`, `shiftwidth=4`, `tabstop=4`,
`smartindent`.

Standalone-only (behind `not vim.g.vscode`, ignored by VS Code):
`number`, `relativenumber`, `cursorline`, `signcolumn=yes`, `scrolloff=8`,
`wrap=false`, `termguicolors`, `splitright`, `splitbelow`.

System clipboard is **not** auto-synced; `<leader>y`/`<leader>Y` reach it
explicitly. Toggle line for `clipboard=unnamedplus` is present but commented out.

## VS Code `settings.json` changes

Edited `C:\Users\PatrickOwens\AppData\Roaming\Code\User\settings.json` because
scroll margin and line numbers are owned by VS Code, not Neovim (so the nvim
options above don't apply in VS Code):

```jsonc
"editor.cursorSurroundingLines": 8,      // Vim scrolloff equivalent (set to 999 for always-centered)
"editor.cursorSurroundingLinesStyle": "all",
"editor.lineNumbers": "relative"         // Vim relativenumber (shows absolute on current line)
```

This is the replacement for the standalone-only `<C-d>zz` / `nzzzv` centering and
`relativenumber` — those don't work in VS Code because VS Code owns scrolling.
(Initially added as `999` for always-centered; adjusted to `8` to match
`scrolloff`.)

---

## Keybindings

Leader is `<space>`.

### Universal — buffer/register ops, work in VS Code and standalone

| Keys | Mode | Maps to |
| --- | --- | --- |
| `<Esc>` | n | `:nohlsearch` — clear search highlight |
| `<` / `>` | x | `<gv` / `>gv` — indent, keep selection |
| `<leader>p` | x | `"_dP` — paste over selection without losing register |
| `<leader>d` | n, x | `"_d` — delete to black-hole register |
| `<leader>y` | n, x | `"+y` — yank to system clipboard |
| `<leader>Y` | n | `"+Y` — yank line to system clipboard |
| `J` | n | `mzJ\`z` — join lines, keep cursor put |
| `Q` | n | `<nop>` — disable Ex mode |

### VS Code only — code navigation & actions

| Keys | Mode | VS Code command |
| --- | --- | --- |
| `gd` | n | `editor.action.revealDefinition` |
| `gD` | n | `editor.action.revealDeclaration` |
| `gr` | n | `editor.action.goToReferences` |
| `gi` | n | `editor.action.goToImplementation` |
| `gy` | n | `editor.action.goToTypeDefinition` |
| `K` | n | `editor.action.showHover` |
| `[d` / `]d` | n | `editor.action.marker.prev` / `.next` — diagnostics |
| `<leader>cr` | n | `editor.action.rename` |
| `<leader>ca` | n, x | `editor.action.quickFix` — code action |
| `<leader>cf` | n / x | `editor.action.formatDocument` / `formatSelection` |
| `<leader>cd` | n | `editor.action.marker.next` — show diagnostic |
| `<leader>cp` | n | `editor.action.peekDefinition` |
| `<leader>cR` | n | `editor.action.refactor` |
| `<leader>cs` | n | `editor.action.sourceAction` — organize imports, etc. |
| `gcc` | n | `editor.action.commentLine` — toggle line comment |
| `gc` | x | `editor.action.commentLine` — toggle comment on selection |

> `gc{motion}` (operator) still uses Neovim's built-in commenting; only `gcc`
> and visual `gc` are routed to VS Code.

### VS Code only — files, search, panels

| Keys | Mode | VS Code command |
| --- | --- | --- |
| `<leader><leader>` / `<leader>ff` | n | `workbench.action.quickOpen` — find file |
| `<leader>fg` | n | `workbench.action.findInFiles` |
| `<leader>fs` | n | `workbench.action.gotoSymbol` |
| `<leader>fc` | n | `workbench.action.showCommands` — command palette |
| `<leader>fr` | n | `workbench.action.quickOpenRecent` |
| `<leader>w` | n | `workbench.action.files.save` |
| `<leader>e` | n | `workbench.action.toggleSidebarVisibility` |
| `<leader>xx` | n | `workbench.actions.view.problems` — problems panel |

### VS Code only — editors, windows, terminal, git

| Keys | Mode | VS Code command |
| --- | --- | --- |
| `<S-h>` / `<S-l>` | n | `workbench.action.previousEditor` / `nextEditor` |
| `<leader>bd` | n | `workbench.action.closeActiveEditor` |
| `<C-h/j/k/l>` | n | `workbench.action.focus{Left,Below,Above,Right}Group` |
| `<leader>sv` | n | `workbench.action.splitEditor` — split right |
| `<leader>sh` | n | `workbench.action.splitEditorDown` — split down |
| `<leader>sx` | n | `workbench.action.closeEditorsInGroup` — close split |
| `<leader>tt` | n | `workbench.action.terminal.toggleTerminal` |
| `]c` / `[c` | n | `workbench.action.editor.nextChange` / `previousChange` |
| `<leader>gg` | n | `workbench.view.scm` — source control |

### Standalone Neovim only (`else` branch — inactive in VS Code)

| Keys | Mode | Maps to |
| --- | --- | --- |
| `J` / `K` | x | `:m` — move selection down / up |
| `<C-d>` / `<C-u>` | n | `<C-d>zz` / `<C-u>zz` — half-page + center |
| `n` / `N` | n | `nzzzv` / `Nzzzv` — search + center |

### Plugin keys

| Keys | Mode | Action |
| --- | --- | --- |
| `s` | n, x, o | flash jump |
| `r` | o | flash remote |
| `S` / `R` | (standalone only) | flash treesitter / treesitter search |
| `ys{motion}{char}` | n | nvim-surround: add surround |
| `yss{char}` | n | surround whole line |
| `ds{char}` / `cs{old}{new}` | n | delete / change surround |
| `S{char}` | x | surround selection |

---

## Known gotchas / decisions

- **`<S-h>` / `<S-l>`** shadow Vim's default H/L (top/bottom of viewport). Switch
  to `[b` / `]b` in `keymaps.lua` if you'd rather keep H/L.
- **`]c` / `[c`** override Vim's diff-mode change motions — irrelevant outside
  diff mode in VS Code.
- **flash + nvim-surround conflict:** flash binds `s` in operator-pending mode,
  but surround's `ds`/`cs`/`ys` are longer mappings and win, so `d`+flash-`s` and
  `c`+flash-`s` are effectively shadowed. flash `s` in normal/visual is fine.
- **flash labels** render via extmarks; they show in most vscode-neovim setups,
  but if letters ever fail to appear, delete `lua/plugins/flash.lua` (the jump
  still works, you just lose the labels).
- **Centering & relativenumber** are handled by VS Code settings (see above), not
  Neovim, because VS Code owns the viewport.

## How to extend

Add more VS Code commands: find a command id via the Command Palette
(gear icon -> "Copy Command ID"), then in `keymaps.lua` (inside the
`if vim.g.vscode` block):

```lua
map("n", "<lhs>", function() require("vscode").action("the.command.id") end, { desc = "..." })
```

Use `require("vscode").call(...)` instead of `.action(...)` if it must run
synchronously. The module is `require("vscode")` (the old `vscode-neovim` name is
deprecated).

---

## Appendix — complete keybinding reference

Every binding in one flat table. Modes: `n` normal, `x` visual, `o` operator-pending.
Scope: **Universal** (everywhere), **VS Code** (only when `vim.g.vscode`),
**Standalone** (only outside VS Code), or the plugin name.

| Keys | Mode | Scope | Maps to |
| --- | --- | --- | --- |
| `<Esc>` | n | Universal | `:nohlsearch` — clear search highlight |
| `<` | x | Universal | `<gv` — indent left, keep selection |
| `>` | x | Universal | `>gv` — indent right, keep selection |
| `<leader>p` | x | Universal | `"_dP` — paste over selection without losing register |
| `<leader>d` | n, x | Universal | `"_d` — delete to black-hole register |
| `<leader>y` | n, x | Universal | `"+y` — yank to system clipboard |
| `<leader>Y` | n | Universal | `"+Y` — yank line to system clipboard |
| `J` | n | Universal | `mzJ\`z` — join lines, keep cursor |
| `Q` | n | Universal | `<nop>` — disable Ex mode |
| `gd` | n | VS Code | `editor.action.revealDefinition` — go to definition |
| `gD` | n | VS Code | `editor.action.revealDeclaration` — go to declaration |
| `gr` | n | VS Code | `editor.action.goToReferences` — references |
| `gi` | n | VS Code | `editor.action.goToImplementation` — implementation |
| `gy` | n | VS Code | `editor.action.goToTypeDefinition` — type definition |
| `K` | n | VS Code | `editor.action.showHover` — hover |
| `[d` | n | VS Code | `editor.action.marker.prev` — previous diagnostic |
| `]d` | n | VS Code | `editor.action.marker.next` — next diagnostic |
| `<leader>cr` | n | VS Code | `editor.action.rename` — rename symbol |
| `<leader>ca` | n, x | VS Code | `editor.action.quickFix` — code action |
| `<leader>cf` | n | VS Code | `editor.action.formatDocument` — format document |
| `<leader>cf` | x | VS Code | `editor.action.formatSelection` — format selection |
| `<leader>cd` | n | VS Code | `editor.action.marker.next` — show diagnostic |
| `<leader>cp` | n | VS Code | `editor.action.peekDefinition` — peek definition |
| `<leader>cR` | n | VS Code | `editor.action.refactor` — refactor menu |
| `<leader>cs` | n | VS Code | `editor.action.sourceAction` — source action |
| `gcc` | n | VS Code | `editor.action.commentLine` — toggle line comment |
| `gc` | x | VS Code | `editor.action.commentLine` — toggle comment on selection |
| `<leader><leader>` | n | VS Code | `workbench.action.quickOpen` — find file |
| `<leader>ff` | n | VS Code | `workbench.action.quickOpen` — find file |
| `<leader>fg` | n | VS Code | `workbench.action.findInFiles` — find in files |
| `<leader>fs` | n | VS Code | `workbench.action.gotoSymbol` — symbol in file |
| `<leader>fc` | n | VS Code | `workbench.action.showCommands` — command palette |
| `<leader>fr` | n | VS Code | `workbench.action.quickOpenRecent` — recent files |
| `<leader>w` | n | VS Code | `workbench.action.files.save` — save |
| `<leader>e` | n | VS Code | `workbench.action.toggleSidebarVisibility` — toggle sidebar |
| `<leader>xx` | n | VS Code | `workbench.actions.view.problems` — problems panel |
| `<S-h>` | n | VS Code | `workbench.action.previousEditor` — previous editor |
| `<S-l>` | n | VS Code | `workbench.action.nextEditor` — next editor |
| `<leader>bd` | n | VS Code | `workbench.action.closeActiveEditor` — close editor |
| `<C-h>` | n | VS Code | `workbench.action.focusLeftGroup` |
| `<C-j>` | n | VS Code | `workbench.action.focusBelowGroup` |
| `<C-k>` | n | VS Code | `workbench.action.focusAboveGroup` |
| `<C-l>` | n | VS Code | `workbench.action.focusRightGroup` |
| `<leader>sv` | n | VS Code | `workbench.action.splitEditor` — split right |
| `<leader>sh` | n | VS Code | `workbench.action.splitEditorDown` — split down |
| `<leader>sx` | n | VS Code | `workbench.action.closeEditorsInGroup` — close split |
| `<leader>tt` | n | VS Code | `workbench.action.terminal.toggleTerminal` — toggle terminal |
| `]c` | n | VS Code | `workbench.action.editor.nextChange` — next git change |
| `[c` | n | VS Code | `workbench.action.editor.previousChange` — previous git change |
| `<leader>gg` | n | VS Code | `workbench.view.scm` — source control |
| `J` | x | Standalone | `:m '>+1<CR>gv=gv` — move selection down |
| `K` | x | Standalone | `:m '<-2<CR>gv=gv` — move selection up |
| `<C-d>` | n | Standalone | `<C-d>zz` — half-page down + center |
| `<C-u>` | n | Standalone | `<C-u>zz` — half-page up + center |
| `n` | n | Standalone | `nzzzv` — next match + center |
| `N` | n | Standalone | `Nzzzv` — previous match + center |
| `s` | n, x, o | flash.nvim | flash jump |
| `r` | o | flash.nvim | flash remote |
| `S` | n, x, o | flash.nvim (standalone) | flash treesitter |
| `R` | o, x | flash.nvim (standalone) | treesitter search |
| `ys{motion}{char}` | n | nvim-surround | add surround |
| `yss{char}` | n | nvim-surround | surround whole line |
| `ds{char}` | n | nvim-surround | delete surround |
| `cs{old}{new}` | n | nvim-surround | change surround |
| `S{char}` | x | nvim-surround | surround selection |
