-- nvim-surround — add/change/delete surrounding pairs (quotes, brackets, tags).
-- A maintained Lua reimplementation of tpope/vim-surround. Pure buffer edits, so
-- it works perfectly under vscode-neovim.
--
-- Cheat sheet:
--   ys{motion}{char}  add surround        e.g. ysiw"  -> wraps word in "
--   yss{char}         surround whole line
--   ds{char}          delete surround     e.g. ds"
--   cs{old}{new}      change surround     e.g. cs"'
--   S{char}           (visual) surround the selection

return {
  "kylechui/nvim-surround",
  version = "*", -- use the latest stable release
  event = "VeryLazy",
  opts = {},
}
