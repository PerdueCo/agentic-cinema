# Team Plan

*Written August 8, 2026. Submission deadline: 2:00 PM PT, September 7, 2026
(30 days out).*

## New team member freeze: August 24, 2026

No new crew members join the project after this date. This is a project
decision, not a Devpost rule — Devpost's own team feature has no lock date,
only the 4-person cap.

**Why August 24 specifically:** it splits the remaining 30 days roughly in
half — 16 days before it, 14 days after.

- The 16 days before the freeze are for finding and onboarding people while
  there's still enough runway left for a new person's work to matter.
- The 14 days after are protected for integration, testing, the demo video,
  and submission polish — without the overhead of onboarding someone new
  mid-crunch.

If someone exceptional applies after August 24, the honest answer is "join
us for the next thing we build" — not a exception to this date. A late
addition who can't meaningfully contribute before the deadline adds
coordination cost without adding real progress.

## Roles

Not every contributor needs to write code. Four roles, only one of which
requires it:

### Crew (Builder)
Contributes code to one or more agents, following the established pattern:
typed input, typed output, a real API call, a mocked test. See
`docs/onboarding/NewDeveloperGuide.md` for the actual first task.

### Mentor
No code contribution required. Sanity-checks the architecture, keeps scope
honest, and flags anything drifting outside the Parallel track's allowed
tooling. See `docs/onboarding/MentorGuide.md` — already written, ready to
send the moment someone says yes.

### QC (Quality Control)
Reviews things before they're called done, not after. Concretely:
- Confirms every new agent's Google Cloud / Parallel calls are genuinely
  called at runtime, not just described in a docstring or README
- Runs `pytest tests/ -q` on every PR before it's merged
- Checks the demo video for third-party logos or unlicensed content before
  it's submitted
- Does one full pass of the submission package against the official rules
  before September 7

This role matters most in the final two weeks, so it's fine for a QC
person to join later than other roles — right up to the freeze date.

### Student Observer
No code, no formal review responsibility. Sits in on progress, reads the
docs as a genuine newcomer would, and says when something doesn't make
sense. The single most useful thing this role can do: try to follow
`NewDeveloperGuide.md` from a clean clone and report exactly where they get
stuck. If a newcomer can't follow it, a judge skimming the repo can't
either.

## Weekly milestones to submission

| Week | Focus |
|---|---|
| Aug 8 – 14 | Budget Agent built, tested, pushed (same pattern as Research and Scheduling). Example frontend prototype and this plan added to the repo. Crew recruitment continues. |
| Aug 15 – 21 | Producer Agent (or next agent in sequence). Any new crew members onboarded via Mentor Guide / New Developer Guide. |
| Aug 22 – 24 | **Freeze date lands Aug 24.** Existing team's scope is final from here. |
| Aug 25 – 31 | Integration and testing pass. QC review of everything built so far. Real hosting (e.g. Cloud Run) stood up if capacity allows. Demo video scripted. |
| Sep 1 – 6 | Demo video recorded and edited (≤3 min, captioned, no third-party branding). Devpost submission text finalized — elevator pitch, Story, Built With tags. Full dry run of the submission before the deadline. |
| Sep 7 | Submit before 2:00 PM PT. |

## Honest risk to name now, not later

This plan assumes roughly one agent per week solo, or faster with crew
help. If that pace slips, the thing to cut first is the number of agents,
not the quality bar on the ones that exist — two or three agents that are
genuinely real and tested is a stronger submission than six that are
half-working. That tradeoff is worth deciding on purpose, not discovering
in the last week.
