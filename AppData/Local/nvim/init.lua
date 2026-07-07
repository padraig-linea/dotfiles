-- Neovim configuration, optimized for the asvetliakov/vscode-neovim extension.
--
-- Mental model: inside VS Code, Neovim only drives motions / editing / text
-- objects / registers / macros. VS Code owns everything else (the UI, LSP,
-- completion, file tree, search, terminal, scrolling, line numbers, ...).
-- So this config keeps Neovim lean and routes UI/LSP/file actions to VS Code
-- commands via `require("vscode").action(...)`.
--
-- It also degrades gracefully if you ever open Neovim outside VS Code: anything
-- VS Code-specific is gated behind `vim.g.vscode`.

-- Leader must be set before lazy.nvim and any plugin keymaps load.
vim.g.mapleader = " "
vim.g.maplocalleader = " "

require("config.options")
require("config.keymaps")
require("config.lazy")
