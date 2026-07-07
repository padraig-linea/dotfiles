-- flash.nvim — jump anywhere on screen with a couple of keystrokes.
--
-- Works in vscode-neovim for the core `s` jump. The treesitter-based modes
-- (`S`, `R`) need nvim-treesitter, which isn't available under VS Code, so they
-- are only bound in standalone Neovim.
--
-- Note: flash draws its jump labels with extmarks. vscode-neovim renders these
-- in most setups, but if the labels ever fail to show, remove this file (the
-- jump still happens; you just won't see the letters).

return {
  "folke/flash.nvim",
  event = "VeryLazy",
  opts = {
    modes = {
      -- Don't hijack the regular `/` search.
      search = { enabled = false },
      -- Enhance f/t/F/T with multi-line, labeled jumps.
      char = { enabled = true },
    },
  },
  keys = function()
    local keys = {
      { "s", mode = { "n", "x", "o" }, function() require("flash").jump() end, desc = "Flash jump" },
      { "r", mode = "o", function() require("flash").remote() end, desc = "Remote flash" },
    }
    if not vim.g.vscode then
      vim.list_extend(keys, {
        { "S", mode = { "n", "x", "o" }, function() require("flash").treesitter() end, desc = "Flash Treesitter" },
        { "R", mode = { "o", "x" }, function() require("flash").treesitter_search() end, desc = "Treesitter search" },
      })
    end
    return keys
  end,
}
