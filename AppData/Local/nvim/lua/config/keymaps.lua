-- Keymaps. Leader (<space>) is set in init.lua before this file loads.

local map = vim.keymap.set

--------------------------------------------------------------------------------
-- Universal maps — pure buffer/register operations that work identically in
-- VS Code and standalone Neovim.
--------------------------------------------------------------------------------

-- Clear search highlight (normal mode only, so it never interferes with insert).
map("n", "<Esc>", "<cmd>nohlsearch<CR>", { desc = "Clear search highlight" })

-- Keep the selection after indenting in visual mode.
map("x", "<", "<gv", { desc = "Indent left (keep selection)" })
map("x", ">", ">gv", { desc = "Indent right (keep selection)" })

-- Paste over a selection without clobbering the yank register.
map("x", "<leader>p", [["_dP]], { desc = "Paste over (keep register)" })

-- Delete into the black-hole register (don't touch the yank register).
map({ "n", "x" }, "<leader>d", [["_d]], { desc = "Delete (black hole)" })

-- Yank to the system clipboard explicitly.
map({ "n", "x" }, "<leader>y", [["+y]], { desc = "Yank to system clipboard" })
map("n", "<leader>Y", [["+Y]], { desc = "Yank line to system clipboard" })

-- Join lines but keep the cursor where it is.
map("n", "J", "mzJ`z", { desc = "Join lines (keep cursor)" })

-- Disable Ex mode.
map("n", "Q", "<nop>")

if vim.g.vscode then
  ------------------------------------------------------------------------------
  -- VS Code mode — route UI / LSP / file / window actions to VS Code commands.
  ------------------------------------------------------------------------------
  local vscode = require("vscode")

  -- Fire-and-forget a VS Code command (async, like the old VSCodeNotify).
  local function act(name)
    return function()
      vscode.action(name)
    end
  end

  -- Move selected lines up/down — VS Code re-indents reliably, unlike the
  -- `:m` + `gv=gv` trick which can desync the buffer in VS Code.
  map("x", "J", act("editor.action.moveLinesDownAction"), { desc = "Move selection down" })
  map("x", "K", act("editor.action.moveLinesUpAction"), { desc = "Move selection up" })

  -- LSP / code navigation
  map("n", "gd", act("editor.action.revealDefinition"), { desc = "Go to definition" })
  map("n", "gD", act("editor.action.revealDeclaration"), { desc = "Go to declaration" })
  map("n", "gr", act("editor.action.goToReferences"), { desc = "Go to references" })
  map("n", "gi", act("editor.action.goToImplementation"), { desc = "Go to implementation" })
  map("n", "gy", act("editor.action.goToTypeDefinition"), { desc = "Go to type definition" })
  map("n", "K", act("editor.action.showHover"), { desc = "Hover" })
  map("n", "[d", act("editor.action.marker.prev"), { desc = "Previous diagnostic" })
  map("n", "]d", act("editor.action.marker.next"), { desc = "Next diagnostic" })

  -- Code actions (under <leader>c = "code")
  map("n", "<leader>cr", act("editor.action.rename"), { desc = "Rename symbol" })
  map({ "n", "x" }, "<leader>ca", act("editor.action.quickFix"), { desc = "Code action" })
  map("n", "<leader>cf", act("editor.action.formatDocument"), { desc = "Format document" })
  map("x", "<leader>cf", act("editor.action.formatSelection"), { desc = "Format selection" })
  map("n", "<leader>cd", act("editor.action.marker.next"), { desc = "Show diagnostic" })

  -- Files & search (under <leader>f = "find")
  map("n", "<leader><leader>", act("workbench.action.quickOpen"), { desc = "Find file" })
  map("n", "<leader>ff", act("workbench.action.quickOpen"), { desc = "Find file" })
  map("n", "<leader>fg", act("workbench.action.findInFiles"), { desc = "Find in files" })
  map("n", "<leader>fs", act("workbench.action.gotoSymbol"), { desc = "Find symbol in file" })
  map("n", "<leader>w", act("workbench.action.files.save"), { desc = "Save file" })
  map("n", "<leader>e", act("workbench.action.toggleSidebarVisibility"), { desc = "Toggle sidebar" })

  -- Editor (tab) navigation. Note: this shadows the default H/L (top/bottom of
  -- viewport). Swap to "[b" / "]b" if you'd rather keep H/L.
  map("n", "<S-h>", act("workbench.action.previousEditor"), { desc = "Previous editor" })
  map("n", "<S-l>", act("workbench.action.nextEditor"), { desc = "Next editor" })
  map("n", "<leader>bd", act("workbench.action.closeActiveEditor"), { desc = "Close editor" })

  -- Move focus between editor groups (splits).
  map("n", "<C-h>", act("workbench.action.focusLeftGroup"), { desc = "Focus left group" })
  map("n", "<C-l>", act("workbench.action.focusRightGroup"), { desc = "Focus right group" })
  map("n", "<C-k>", act("workbench.action.focusAboveGroup"), { desc = "Focus above group" })
  map("n", "<C-j>", act("workbench.action.focusBelowGroup"), { desc = "Focus below group" })

  -- Splits (under <leader>s = "split")
  map("n", "<leader>sv", act("workbench.action.splitEditor"), { desc = "Split editor right" })
  map("n", "<leader>sh", act("workbench.action.splitEditorDown"), { desc = "Split editor down" })
  map("n", "<leader>sx", act("workbench.action.closeEditorsInGroup"), { desc = "Close split" })

  -- Terminal
  map("n", "<leader>tt", act("workbench.action.terminal.toggleTerminal"), { desc = "Toggle terminal" })

  -- Commenting — routed to VS Code so it's language-aware (handles JSX, embedded
  -- languages, etc.). Operator-style `gc{motion}` still uses Neovim's built-in.
  map("n", "gcc", act("editor.action.commentLine"), { desc = "Toggle comment line" })
  map("x", "gc", act("editor.action.commentLine"), { desc = "Toggle comment" })

  -- More code actions (under <leader>c = "code")
  map("n", "<leader>cp", act("editor.action.peekDefinition"), { desc = "Peek definition" })
  map("n", "<leader>cR", act("editor.action.refactor"), { desc = "Refactor" })
  map("n", "<leader>cs", act("editor.action.sourceAction"), { desc = "Source action (organize imports, ...)" })

  -- Git changes (under <leader>g = "git")
  map("n", "]c", act("workbench.action.editor.nextChange"), { desc = "Next change" })
  map("n", "[c", act("workbench.action.editor.previousChange"), { desc = "Previous change" })
  map("n", "<leader>gg", act("workbench.view.scm"), { desc = "Source control" })

  -- Command palette & recent files (under <leader>f = "find")
  map("n", "<leader>fc", act("workbench.action.showCommands"), { desc = "Command palette" })
  map("n", "<leader>fr", act("workbench.action.quickOpenRecent"), { desc = "Recent files" })

  -- Diagnostics list
  map("n", "<leader>xx", act("workbench.actions.view.problems"), { desc = "Problems panel" })
else
  ------------------------------------------------------------------------------
  -- Standalone Neovim fallback — only used if you open nvim outside VS Code.
  ------------------------------------------------------------------------------

  -- Move selected lines up/down.
  map("x", "J", ":m '>+1<CR>gv=gv", { desc = "Move selection down" })
  map("x", "K", ":m '<-2<CR>gv=gv", { desc = "Move selection up" })

  -- Keep the cursor centered while half-paging and searching. (Skipped in
  -- VS Code, where scrolling is handled by VS Code and `zz` behaves differently.)
  map("n", "<C-d>", "<C-d>zz")
  map("n", "<C-u>", "<C-u>zz")
  map("n", "n", "nzzzv")
  map("n", "N", "Nzzzv")
end
