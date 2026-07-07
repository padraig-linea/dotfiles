-- targets.vim — richer text objects (pairs, quotes, separators, arguments).
-- Pure buffer operations, so it works under vscode-neovim.
--
-- A few highlights it adds on top of the built-in text objects:
--   ci,  / ca,    change inside / around a comma-separated argument
--   din( / dan(   delete *next* / *previous* () pair contents
--   ci) ci] ci}   work even when the cursor isn't inside the pair yet
--   I, A          seek to the next/previous instance of a text object

return {
  "wellle/targets.vim",
  event = "VeryLazy",
}
