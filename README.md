# TimeMachine 🕰️ — Valid-Time Memory for AI Agents

**Graph Hacks 2026 (WeMakeDevs × FalkorDB) — Track 2: Agent Memory and Coordination**

An AI agent that remembers not just *what* it believes, but *when* it believed it.
Ask *"What caused the checkout outage?"* → today's answer.
Ask *"What did you believe last Tuesday?"* → the answer it held **then**, with the evidence that changed its mind.

Vector databases can't do this — embeddings have no concept of time. Only a graph with
valid-time edges can reconstruct a past belief state. **Remove FalkorDB and the product
stops working.** That's the point.

## Quick start

```bash
# 1. Start FalkorDB (needs Docker)
docker compose up -d

# 2. Install deps
pip install -r requirements.txt

# 3. Seed the 2-week incident timeline
python -m src.seed

# 4. Run the cinematic demo
python -m src.demo
```

FalkorDB Browser (graph visualisation for your demo video): http://localhost:3000

## Ask it anything

```python
from src.agent import TimeMachineAgent

agent = TimeMachineAgent()
agent.connect()

agent.ask("What caused the checkout outage?")                       # now
agent.ask("What caused the checkout outage?", as_of="2026-10-08")  # time travel
agent.ask("What caused the checkout outage?", as_of="2026-10-05")  # further back
agent.timeline("checkout-outage")                                  # belief history
agent.why_changed("checkout-outage", "2026-10-10")                  # evidence behind a change
agent.ask("What if the traffic report never existed?")             # counterfactual fork
```

## How it works

Every memory edge carries a validity interval:

```
(:Agent)-[:BELIEVES {valid_from, valid_to}]->(:Claim)-[:ABOUT]->(:Topic)
(:Claim)-[:SUPPORTED_BY {valid_from, valid_to}]->(:Evidence)
```

When the agent changes its mind, the old edge is **closed** (`valid_to` set), never deleted.
An "as-of" query filters edges to those valid at time T — reconstructing the exact belief
graph the agent held at that moment. This is the valid-time temporal pattern from
Zep/Graphiti-style memory research, implemented natively in Cypher.

## Project structure

```
├── docker-compose.yml   # FalkorDB in one command
├── requirements.txt
├── .env.example         # optional GEMINI_API_KEY for LLM-polished answers
├── src/
│   ├── graph.py         # connection + schema helpers
│   ├── seed.py          # fictional 2-week incident timeline (the demo dataset)
│   ├── agent.py         # TimeMachineAgent: ask(), timeline(), why_changed()
│   └── demo.py          # rich-powered cinematic CLI demo
└── demo_script.md       # 3-minute judging video script
```

## The demo dataset: "The Checkout Outage"

| Date | Evidence | Agent's belief |
|---|---|---|
| Oct 4 | Cache hit rate 95% → 40% | Cache misconfiguration |
| Oct 7 | DB pool exhausted, 500 waiters | Connection pool exhaustion |
| Oct 10 | Deploy v2.4 halved pool 100 → 50 | Bad deploy v2.4 |
| Oct 14 | Traffic spiked 3× during sale | Traffic spike overwhelmed pool |

Ask on Oct 8 → "connection pool exhaustion". Ask on Oct 5 → "cache misconfiguration".
Same question, different truth — depending on *when* you ask.

## Submission checklist

- [ ] `docker compose up -d` + `python -m src.seed` + `python -m src.demo` all green
- [ ] 2–3 min demo video (see `demo_script.md`) — this is what judges watch
- [ ] Public GitHub repo, clean README
- [ ] dev.to blog post (separate prizes for best blog posts!)
- [ ] Submit before the Oct 18 deadline
