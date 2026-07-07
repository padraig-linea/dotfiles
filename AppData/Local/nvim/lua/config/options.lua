-- Options.
--
-- Under VS Code, most *display* options are ignored (VS Code owns the UI), so we
-- only set behaviour that Neovim still controls there, and put the display-only
-- options behind a `not vim.g.vscode` guard so a standalone Neovim still looks
-- sane.

local opt = vim.opt

--------------------------------------------------------------------------------
-- Behaviour Neovim still drives inside VS Code
--------------------------------------------------------------------------------

-- Search (Neovim still handles `/` and `?` even inside VS Code)
opt.ignorecase = true
opt.smartcase = true
opt.incsearch = true
opt.hlsearch = true

-- Editing
opt.undofile = true   -- persistent undo across sessions
opt.timeoutlen = 400  -- ms to wait for a mapped sequence (e.g. leader chords)
opt.updatetime = 250

-- Indentation (used by `>>`, `<<`, `=`, etc.)
opt.expandtab = true
opt.shiftwidth = 4
opt.tabstop = 4
opt.smartindent = true

-- If you'd rather have `y`/`p` use the system clipboard automatically (handy for
-- copying between VS Code and other apps), uncomment the next line. This config
-- instead keeps registers separate and exposes the system clipboard via
-- <leader>y / <leader>Y (see keymaps.lua).
-- opt.clipboard = "unnamedplus"

--------------------------------------------------------------------------------
-- Display options — only meaningful in standalone Neovim. VS Code ignores these
-- (use VS Code's own settings for line numbers, scrolloff, theme, etc.).
--------------------------------------------------------------------------------
if not vim.g.vscode then
  opt.number = true
  opt.relativenumber = true
  opt.cursorline = true
  opt.signcolumn = "yes"
  opt.scrolloff = 8
  opt.wrap = false
  opt.termguicolors = true
  opt.splitright = true
  opt.splitbelow = true
end
