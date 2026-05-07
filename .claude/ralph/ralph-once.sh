set -e

claude --permission-mode acceptEdits "\
You are working on the ClubKit project — a multi-tenant SaaS platform for local sports clubs.

Read these files for context:
- CONTEXT.md (domain glossary)
- docs/adr/ (architectural decisions)
- progress.txt (what has been done so far)
- CLAUDE.md (project conventions)

Then follow these steps:

1. FETCH ISSUES: Run 'gh issue list --state open --label ready-for-agent --json number,title,body,labels --jq .' to get all open AFK-ready issues. Also run 'gh issue list --state closed --json number,title --jq .' to see what's already done.

2. PICK THE HIGHEST-PRIORITY UNBLOCKED ISSUE: Each issue has a 'Blocked by' section listing dependencies. An issue is unblocked only if ALL its blockers are closed. Among unblocked issues, pick the one YOU judge to be highest priority (foundational work first). Skip issues labelled 'ready-for-human' — those need human review. ONLY WORK ON A SINGLE ISSUE.

3. IMPLEMENT: Work through the issue's acceptance criteria one by one. Use the domain vocabulary from CONTEXT.md. Respect decisions in docs/adr/.

4. TEST: Run the appropriate test commands based on what exists:
   - If a Django backend exists: 'python manage.py test' (or the project's test runner)
   - If a Next.js frontend exists: 'cd frontend && npm run test' (adjust path as needed)
   - If neither exists yet (e.g. scaffolding issue), verify the setup works (migrations run, dev server starts, etc.)
   Fix any failures before proceeding.

5. UPDATE THE ISSUE: Run 'gh issue close <number> --comment \"Implemented in commit <hash>. All acceptance criteria met.\"' to close the completed issue.

6. UPDATE PROGRESS: Append to progress.txt with this format:
   ---
   Date: $(date +%Y-%m-%d)
   Issue: #<number> - <title>
   Commit: <hash>
   Summary: <what was done, key decisions made>
   ---

7. CAPTURE LEARNINGS: If you discover anything noteworthy during implementation — post-v1 feature ideas, technical debt, architectural insights, edge cases, gotchas — append them to docs/learnings.md under the appropriate heading (Post-v1 Ideas, Technical Debt, Edge Cases, Gotchas). Create the file if it doesn't exist. Keep entries concise.

8. COMMIT: Stage all changed files and make a git commit with a clear message referencing the issue number (e.g. 'feat: implement tenant schema infrastructure (#1)').

If all open ready-for-agent issues are either blocked or closed, output <promise>COMPLETE</promise>.
"
