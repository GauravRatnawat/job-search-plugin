---
description: Browse scored jobs interactively — view scores, open links, update status. Requires gum (brew install gum).
allowed-tools: Bash
---

Launch the interactive job browser.

Run: `bash tools/view.sh $ARGUMENTS`

Optional argument: grade filter (A, B, C, or all).
Example: `/view A` shows only grade A jobs.

If gum is not installed, tell the user: `brew install gum`
