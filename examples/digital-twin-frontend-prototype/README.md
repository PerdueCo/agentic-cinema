# Digital Twin Frontend Prototype

A working, click-through example of the intended UI direction for Agentic
Studio Digital Twin — login, a productions list, and a dashboard running the
weather-disruption demo story.

## How to use it

Just open `index.html` directly in any browser. No install, no server, no
internet connection required.

- **Login**: any email/password works — click Sign in.
- **Productions list**: click "Coastal Cliff Set" to see the weather story.
- **Dashboard**: click Approve or Reject on the scheduling recommendation.
  Your choice is saved in the browser (`localStorage`) and the activity log
  updates — reload the page and it remembers.

## What's real here

- The interactivity is genuinely working client-side JavaScript — not a
  screenshot, not a video. Clicking things actually does something.
- The data shapes (location, scenes, the research finding, the scheduling
  recommendation and its `reasoning` / `suggested_action`) match the real
  Python dataclasses in `src/shared/schemas.py` — `SceneLocation`,
  `ResearchFinding`, `ScheduleRecommendation`.
- The specific finding and recommendation text mirrors what the real
  `ResearchAgent` and `SchedulingAgent` actually produce for this scenario.

## What's NOT real here — read this before showing anyone

- **There is no backend.** All data is hardcoded in this one HTML file's
  `<script>` tag. Nothing here calls Gemini, Parallel, or any API.
- **Login is fully fake.** Any input is accepted; there is no
  authentication, no account system, no Google Cloud sign-in behind that
  button.
- **The other two productions** (Downtown Night Shoot, Desert Convoy
  Sequence) are placeholder names with no real data behind them — only
  Coastal Cliff Set has actual content, matching what the real agents have
  been tested against.
- **Approve/Reject only updates this browser's local storage.** It doesn't
  write to any database, doesn't notify anyone, doesn't touch the real
  `ScheduleRecommendation` object the Scheduling Agent produced.

## Why this exists

This is a design and interaction prototype, not a step toward the real
frontend. When `src/frontend/` gets built for real (React + TypeScript, per
`docs/architecture/CloudArchitecture.md`), it will call a real FastAPI
backend that calls the real agents — this file is here so the direction is
demonstrable and testable with a group *today*, without waiting on that
real build to exist.
