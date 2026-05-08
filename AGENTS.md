# Monorepo

* this repository is a loose collection of independent tools
* single-script tools sit in the root; multi-files tools like `vireg` sit in their own folder

# github commits

* add this suffix at the end of the first line of each commit: `[opencode:kimi-k2.6]`
* use Conventional Commits prefixes, e.g. `fix(vireg):`, `feat(static_site):`. Most common prefix types are `fix`, `feat`, `doc`, `style`, `refactor`, `perf`, `ci` and `test`
* add `!` after `feat` or `fix` for breaking changes, e.g. `feat(vireg)!:`
* never do git push; it should remain manual
* at the end of any code modification, propose a git add (if relevant) and a git commit message to be accepted manually
* never commit, move, remove or add without user confirmation

# Coding style

* keep the code simple and readable
* break problem down into small functions/methods
* if not obvious from its name, succinctly document what a method or function does and returns
* only add inline comments when necessary
* returned variable is always called `ret`
* only call `return` at the beginning of a function or at the end, never in the middle
* keep all literals into capitalised constants declared near the top of the file, after the imports
* only use type hints in function signatures
