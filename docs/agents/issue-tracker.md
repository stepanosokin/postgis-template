# Issue tracker

Use `gh` with `stepanosokin/postgis-template` for GitHub Issues. Publish specs and tickets with `gh issue create --title "..." --body-file <file>`. Read tickets with `gh issue view <number> --json number,title,body,labels,comments`. Find open tickets with `gh issue list --state open` and filter by label as needed.

**PRs as a request surface: no.**

## Wayfinding operations

- Create the map as a GitHub issue labelled `wayfinder:map`. Keep notes, decisions, and open questions in its body.
- Add decision tickets as GitHub sub-issues. Record their type with a `wayfinder:<type>` label.
- Record blockers as GitHub issue dependencies. If dependencies are unavailable, list the blocker numbers in the ticket body under `Blocked by`.
- Follow the map's order when choosing the first open, unassigned ticket with no open blockers.
- Assign the ticket to yourself when you claim it. To resolve it, post the answer, close the ticket, and add the decision and ticket link to the map.
