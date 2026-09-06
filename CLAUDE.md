# Project rules — HR-APP (PeopleDesk)

## Git — hard rule, no exceptions

- **Never run any git command** — no `git add`, `git commit`, `git push`, `git stage`, `git rm`, `git checkout` (destructive forms), or any other git subcommand that modifies repo state or history.
- This applies under **every permission mode**, including auto-accept-edits and bypass/"yolo" mode. File edits may be auto-accepted; git operations are never auto-accepted or silently run.
- All commits, staging, and pushes are done manually by the repo owner. If a task seems to require a git operation to be "complete," stop short of it and report what's ready for the owner to commit — do not ask "should I commit this?" as a way around the rule.
- Read-only git commands are fine or when explicitly asked for status/history — for example, `git status`, `git diff`, `git log`. The rule is about hard changes to repo state.

## Scope discipline

- Only touch the files/areas explicitly named in the current task. Don't refactor, rename, reformat, or "improve" unrelated code while working on something else — flag it instead and let the owner decide.
- Don't add new dependencies without calling it out explicitly and explaining why (e.g. "this needs X because Y" as its own line in the report), so the owner can veto before it's in `package.json`/`requirements.txt`.
- Don't change routes, data-fetching logic, database schema, or API contracts as a side effect of a visual/styling task, or vice versa. State clearly if a task turns out to require crossing that boundary.

## Verification before reporting done

- For any change touching the frontend: run `npm run build` in `web/` and confirm zero TypeScript errors before reporting completion.
- For any change touching the backend: confirm the app imports cleanly (e.g. `python -c "from app.main import app"`) and, where relevant, that migrations/tests still pass.
- For Docker/infra changes: actually run `docker compose up --build` and confirm the full stack reaches a healthy state (not just that files were edited) before calling something verified.
- Report actual command output, not a summary claim of success — "it works" without the output attached is not sufficient.

## Working tree hygiene

- Leave the working tree in a clean, reviewable state: no stray build artifacts, temp files, or cache files (e.g. `tsconfig.tsbuildinfo`) left behind from verification steps.
- At the end of a task, state plainly what files were modified/added, matching what `git status` would show, so the owner knows exactly what to review before committing.