# Demo video script — 3 minutes (this is what the judges watch)

Record: terminal running `python -m src.demo` + FalkorDB Browser (localhost:3000)
showing the graph. No live coding on camera.

## 0:00–0:20 — The problem
> "AI agents forget. Worse — when they change their mind, the old belief is gone.
> Ask any agent what it believed last Tuesday and you get a shrug. Vector memory
> stores what's *similar*. It can't store what was *true when*."

## 0:20–0:50 — The idea
> "TimeMachine gives agents valid-time memory on FalkorDB. Every belief is an edge
> with a validity interval. When the agent changes its mind, the old edge is closed —
> never deleted. So you can time-travel: ask what the agent believed on any date,
> and FalkorDB reconstructs that exact belief state with one Cypher query."

Show the graph in FalkorDB Browser: Agent → BELIEVES(valid_from, valid_to) → Claims.

## 0:50–1:50 — The demo (run `python -m src.demo`)
1. "What caused the checkout outage?" → *Traffic spike overwhelmed the pool* (today's belief)
2. Same question, **as of Oct 8** → *Connection pool exhaustion*
3. Same question, **as of Oct 5** → *Cache misconfiguration*
4. "Why did you change your mind on Oct 10?" → *Deploy v2.4 halved the pool size — PR #2214*
5. Show the belief timeline table.

> "Same question. Three different true answers — depending on *when* you ask."

## 1:50–2:10 — The twist: what-if time travel
> "And here's the twist. What if that traffic report never landed on my desk?
> I fork the belief graph, delete that evidence, and recompute. In that alternate
> timeline, I'd still believe the bad deploy caused the outage. Same agent, same
> graph — a different past, a different truth."

## 2:10–2:40 — Why FalkorDB (say this out loud — sponsors listen)
> "Remove FalkorDB and this product dies — the decoration test. A vector DB
> fundamentally cannot answer as-of questions; embeddings have no time axis.
> This needs real graph traversal with validity filtering, at in-memory speed,
> inside the agent loop — plus native multi-graph forks for the what-if.
> That's FalkorDB."

## 2:40–3:00 — Close
> "TimeMachine: memory with a past tense. Track 2 — Agent Memory and Coordination.
> Code on GitHub, try the live demo. Thanks!"

## Checklist
- [ ] Terminal font large enough to read at 720p
- [ ] FalkorDB Browser graph visible at 0:20–0:50
- [ ] Say the track name + "FalkorDB" out loud (judges skim)
- [ ] Under 3 minutes — cut the timeline table if running long
- [ ] Upload unlisted to YouTube, link in submission + repo README
