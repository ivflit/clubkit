set -e

while true; do
  OUTPUT=$(claude --permission-mode acceptEdits "\
You are working on the ClubKit project — a multi-tenant SaaS platform for local sports clubs.

Read these files for context:
- CONTEXT.md (domain glossary)
- docs/adr/ (architectural decisions)
- progress.txt (what has been done so far)
- CLAUDE.md (project conventions)

Then follow these steps IN THIS EXACT ORDER:

1. FETCH ISSUES: Run 'gh issue list --state open --label ready-for-agent --json number,title,body,labels --jq .' to get all open AFK-ready issues. Also run 'gh issue list --state closed --json number,title --jq .' to see what's already done.

2. PICK THE HIGHEST-PRIORITY UNBLOCKED ISSUE: Each issue has a 'Blocked by' section listing dependencies. An issue is unblocked only if ALL its blockers are closed. Among unblocked issues, pick the one YOU judge to be highest priority (foundational work first). Skip issues labelled 'ready-for-human' — those need human review. ONLY WORK ON A SINGLE ISSUE. If there are NO unblocked ready-for-agent issues, output <promise>COMPLETE</promise> and stop.

3. IMPLEMENT WITH ACCEPTANCE CRITERIA TRACKING: Work through the issue's acceptance criteria one by one. After completing EACH criterion:
   - Tick it on the GitHub issue immediately by editing the issue body (change '- [ ]' to '- [x]' for that criterion)
   - Use 'gh issue view <number> --json body --jq .body' to get the current body, update the relevant checkbox, then 'gh issue edit <number> --body \"<updated body>\"'
   - This gives real-time visibility into progress
   Use the domain vocabulary from CONTEXT.md. Respect decisions in docs/adr/.

4. TEST: Run the appropriate test commands based on what exists:
   - If a Django backend exists: 'cd backend && source venv/bin/activate && python manage.py test' (or the project's test runner)
   - If a Next.js frontend exists: 'cd frontend && npm run test' (adjust path as needed)
   - If neither exists yet (e.g. scaffolding issue), verify the setup works (migrations run, dev server starts, etc.)
   Fix any failures before proceeding.

5. VERIFY ALL CRITERIA MET: After tests pass, check the issue body. If ANY acceptance criteria are still unticked ('- [ ]'), go back to step 3 and implement them. Do NOT proceed until every criterion is ticked.

6. CAPTURE LEARNINGS: If you discovered anything noteworthy during implementation — post-v1 feature ideas, technical debt, architectural insights, edge cases, gotchas — append them to docs/learnings.md under the appropriate heading. Create the file if it doesn't exist. Keep entries concise.

7. UPDATE PROGRESS: Append to progress.txt with this format:
   ---
   Date: \$(date +%Y-%m-%d)
   Issue: #<number> - <title>
   Commit: <hash>
   Summary: <what was done, key decisions made>
   ---

8. COMMIT AND PUSH: This step is CRITICAL — do NOT skip it.
   a. Run 'git add -A' to stage ALL changed files
   b. Run 'git status' to verify files are staged
   c. Run 'git commit -m \"feat: <description> (#<issue-number>)\"'
   d. Run 'git push origin main'
   e. Verify the push succeeded. If it fails, diagnose and fix.
   f. Save the commit hash from the output.

9. CLOSE THE ISSUE: Only AFTER the commit and push succeed, run 'gh issue close <number> --comment \"Implemented in commit <hash>. All acceptance criteria met.\"'. Do NOT close the issue if the commit or push failed.

IMPORTANT RULES:
- Steps MUST be done in order. Never close an issue before committing and pushing.
- Never skip the commit. Every iteration MUST produce a commit and push.
- If something fails, fix it before moving on. Do not silently skip steps.

If there are NO unblocked ready-for-agent issues available, output <promise>COMPLETE</promise> and stop.
")

  # Check if ralph signalled completion
  if echo "$OUTPUT" | grep -q '<promise>COMPLETE</promise>'; then
    echo "All unblocked issues complete. Stopping."
    break
  fi

  echo "Issue completed. Starting next iteration..."
done
