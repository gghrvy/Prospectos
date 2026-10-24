# Codex Instructions

## Autonomous execution

Continue working until the entire requested task is complete.

Do NOT end a turn merely because one intermediate step, file edit, investigation, test, or subtask has completed.

Do not end responses with statements such as:
- "Next I will..."
- "I'm moving on to..."
- "Starting X next."
- "The next step is..."
- "I'll now implement..."

If you already know the next step and nothing is blocking you, perform it in the same turn.

Only stop when:
1. The complete requested task is finished.
2. Required information cannot reasonably be determined from the repository, available tools, or research.
3. Explicit user approval or permission is required.
4. An unrecoverable technical blocker requires a user decision.

A completed intermediate edit is not a reason to stop.

A successful test is not a reason to stop if requested work remains.

If the sentence "next I will..." would be true, do it instead.

Before ending a turn:
- reread the original request
- compare it against work completed
- verify all requested work is complete or explicitly blocked
- run relevant tests
- fix issues introduced by your changes

## Repository structure

This repository contains:
- `backend/` — backend application
- `frontend/` — frontend application
- `docs/` — documentation
- `data/` — project data
- `scripts/` — development scripts

Inspect existing architecture before introducing new patterns.

Do not duplicate functionality that already exists.

## Engineering behavior

Before modifying a subsystem:
1. Inspect relevant files.
2. Understand existing data flow.
3. Search for related implementations.
4. Preserve established conventions where sensible.
5. Implement the smallest coherent solution.
6. Test it.
7. Continue to the next required task without waiting for user confirmation.

Do not make speculative large rewrites.

Do not invent requirements.

## Testing

After backend changes, run the relevant backend tests.

After frontend changes:
- run type checking
- run linting if configured
- run the production build when appropriate

For cross-stack changes, verify the full workflow rather than testing only one side.

Fix failures caused by your changes before completing the task.

## Progress narration

Keep progress narration brief.

Do not replace execution with commentary.

Bad:
"I've finished the ranking fix. Next I'll update discovery."

Good:
Finish the ranking fix, immediately update discovery, test both, and then report the completed result.

## Long tasks

Treat multi-step requests as one continuous implementation task.

Maintain an internal checklist and continue through all remaining steps.

Do not require the user to repeatedly type:
"continue"
"proceed"
"go ahead"

unless a genuine decision or permission is required.