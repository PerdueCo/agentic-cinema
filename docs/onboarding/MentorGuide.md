# Mentor Guide

*BUILD · DIRECT · ORCHESTRATE · PREMIERE*

Thanks for stepping onto the lot. This is the context you need before our
first real conversation — what this is, where it stands, and where your eye
would matter most.

## What Agentic Cinema is

Agentic Cinema is a movement, not a company: an open invitation for builders
across every discipline — engineering, story, design, sound, motion — to
treat movie-studio roles as the language for multi-agent AI. Instead of one
model trying to do everything, a full crew of specialized agents
collaborates, the way a real production does.

**Agentic Studio Digital Twin** is the hackathon submission that puts that
idea into working code: a living digital twin of a film production, with a
dedicated AI agent over every department — Director, Producer, Scheduler,
Budget, Location, Camera, and more — all sharing one knowledge graph, all
following the same loop: **observe, analyze, recommend, act** — with a human
approving before anything actually happens.

## Where it stands right now — read this before anything else

I'd rather you see the real state than the pitch. As of today:

- **One agent is fully built and pushed**: the Research Agent, which calls
  the Parallel Search API for live, sourced information, then Gemini to
  summarize it. Real code, real tests, genuinely running.
- **The twelve-agent ecosystem is architecture, not yet code.** It's
  designed, documented, and the pattern (typed data contracts, mocked
  tests, runtime-only claims) is proven on the one agent that exists. The
  rest follows that same pattern, one agent at a time.
- **This is a solo build so far.** You're one of the first people seeing it
  from the inside.

If something in the README or the landing page reads as more built than it
is, tell me — that's a gap I'd rather close than leave standing.

## Where your feedback matters most

1. **Architecture sanity-check** — does the Observe → Analyze → Recommend →
   Act loop, and the shared Knowledge Graph pattern, actually hold up as
   more agents get added, or are there seams I can't see yet from inside it.
2. **Scope discipline** — I have a tendency toward ambition (see: twelve
   agents). Help me flag when something's a distraction from getting the
   next agent genuinely working versus real, necessary scope.
3. **Track compliance** — this is entered in the hackathon's Parallel track,
   which means only Google Cloud AI tooling (Gemini, `google-genai`,
   `google-adk`, etc.) and the Parallel Search API are permitted in the
   product itself. If you spot anything drifting outside that, flag it
   immediately — it's a disqualification risk, not just a style note.

## Hackathon boundaries, for context

- **Contest period:** ends 2:00 PM PT, September 7, 2026.
- **AI restriction:** Google Cloud AI tools + Parallel only, in the actual
  runtime code. No other AI vendor tooling anywhere in the shipped product.
- **Repo requirement:** public, MIT-licensed, and every claimed integration
  must be genuinely imported and called in code — not just described.
- **Team:** up to 4 people total, added officially through Devpost's team
  feature once someone's confirmed in.

## Meeting format

Open to whatever cadence works for you — a standing weekly async check-in,
or a single working session, whichever fits. I'd suggest starting with one
conversation covering the architecture and the Research Agent's code
directly, then deciding cadence from there based on how much runway you
have.

Welcome to the crew.

**Clarence Perdue Jr.**
*Data Engineer | Software Engineer | AI & Data Solutions Architect*
