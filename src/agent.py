"""TimeMachineAgent — ask what the agent believes, now or at any point in time.

Works fully offline with answer templates. If GEMINI_API_KEY is set, answers
get polished by Gemini (optional, never required for the demo).
"""
import os
import re

from dotenv import load_dotenv

from . import seed as seed_module
from .graph import connect, as_of_filter

load_dotenv()

TOPIC = "checkout-outage"
FORK_GRAPH = "timemachine_whatif"


class TimeMachineAgent:
    def __init__(self):
        self.db = None
        self.g = None
        self._llm = None

    def connect(self):
        self.db, self.g = connect()
        key = os.getenv("GEMINI_API_KEY")
        if key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=key)
                self._llm = genai.GenerativeModel("gemini-2.0-flash")
            except Exception:
                self._llm = None  # offline mode is fine
        return self

    # ---------- core temporal queries ----------

    def belief_at(self, topic: str, as_of: str) -> dict | None:
        """What did the agent believe about `topic` at time `as_of` (ISO date)?"""
        q = f"""
        MATCH (t:Topic {{name: $topic}})<-[:ABOUT]-(c:Claim)<-[b:BELIEVES]-(a:Agent)
        WHERE {as_of_filter('b', as_of)}
        RETURN c.text AS belief, b.valid_from AS since,
               b.valid_to AS until, a.name AS agent
        """
        rows = self.g.query(q, {"topic": topic}).result_set
        if not rows:
            return None
        belief, since, until, agent = rows[0]
        return {"belief": belief, "since": since, "until": until, "agent": agent}

    def belief_now(self, topic: str) -> dict | None:
        """Current belief = the edge that was never closed."""
        q = """
        MATCH (t:Topic {name: $topic})<-[:ABOUT]-(c:Claim)<-[b:BELIEVES]-(a:Agent)
        WHERE b.valid_to IS NULL
        RETURN c.text AS belief, b.valid_from AS since
        """
        rows = self.g.query(q, {"topic": topic}).result_set
        if not rows:
            return None
        return {"belief": rows[0][0], "since": rows[0][1]}

    def timeline(self, topic: str) -> list[dict]:
        """Full belief history, oldest first."""
        q = """
        MATCH (t:Topic {name: $topic})<-[:ABOUT]-(c:Claim)<-[b:BELIEVES]-(a:Agent)
        RETURN c.text AS belief, b.valid_from AS since, b.valid_to AS until
        ORDER BY b.valid_from
        """
        return [
            {"belief": r[0], "since": r[1], "until": r[2]}
            for r in self.g.query(q, {"topic": topic}).result_set
        ]

    def why_changed(self, topic: str, as_of: str) -> list[dict]:
        """Which evidence supported the belief held at time `as_of`?"""
        q = f"""
        MATCH (t:Topic {{name: $topic}})<-[:ABOUT]-(c:Claim)<-[b:BELIEVES]-(:Agent),
              (c)-[s:SUPPORTED_BY]->(e:Evidence)
        WHERE {as_of_filter('b', as_of)} AND {as_of_filter('s', as_of)}
        RETURN c.text AS belief, e.text AS evidence, e.source AS source,
               e.observed_at AS observed
        """
        return [
            {"belief": r[0], "evidence": r[1], "source": r[2], "observed": r[3]}
            for r in self.g.query(q, {"topic": topic}).result_set
        ]

    def what_if(self, topic: str, remove_evidence_id: str) -> dict:
        """Counterfactual: fork the belief graph (FalkorDB multi-graph), remove
        one evidence, and recompute what the agent would believe instead.

        Returns {"removed": ..., "alternate": ..., "reality": ...}.
        """
        # Fork = rebuild the timeline minus one evidence, in its own graph.
        seed_module.seed(graph_name=FORK_GRAPH, skip={remove_evidence_id})
        fg = self.db.select_graph(FORK_GRAPH)
        rows = fg.query(
            """
            MATCH (t:Topic {name: $topic})<-[:ABOUT]-(c:Claim)<-[b:BELIEVES]-(:Agent)
            WHERE b.valid_to IS NULL
            RETURN c.text AS belief, b.valid_from AS since
            """,
            {"topic": topic},
        ).result_set
        alternate = {"belief": rows[0][0], "since": rows[0][1]} if rows else None

        ev = self.g.query(
            "MATCH (e:Evidence {id: $eid}) RETURN e.text AS t, e.source AS s",
            {"eid": remove_evidence_id},
        ).result_set
        removed = (
            {"text": ev[0][0], "source": ev[0][1]}
            if ev
            else {"text": remove_evidence_id, "source": "unknown"}
        )
        return {"removed": removed, "alternate": alternate,
                "reality": self.belief_now(topic)}

    # ---------- natural-language front ----------

    def ask(self, question: str, as_of: str | None = None) -> str:
        q = question.lower()
        if "what if" in q or "whatif" in q:
            r = self.what_if(TOPIC, "evidence-3")
            answer = (
                f"In reality I believe: \"{r['reality']['belief']}\" "
                f"(since {r['reality']['since']}).\n"
                f"Without the evidence \"{r['removed']['text']}\" "
                f"({r['removed']['source']}), I would instead believe: "
                f"\"{r['alternate']['belief']}\" (since {r['alternate']['since']})."
            )
        elif "why" in q and ("change" in q or "mind" in q):
            date = as_of or self._extract_date(q) or "2026-10-18"
            rows = self.why_changed(TOPIC, date)
            if not rows:
                return f"No belief change recorded around {date}."
            r = rows[0]
            answer = (
                f"On {r['observed']} my belief became: \"{r['belief']}\"\n"
                f"Because: {r['evidence']} (source: {r['source']})"
            )
        elif "timeline" in q or "history" in q:
            rows = self.timeline(TOPIC)
            lines = [
                f"- {r['since']} → {r['until'] or 'now'}: {r['belief']}" for r in rows
            ]
            answer = "My belief history on the checkout outage:\n" + "\n".join(lines)
        elif as_of:
            b = self.belief_at(TOPIC, as_of)
            answer = (
                f"On {as_of} I believed: \"{b['belief']}\" (held since {b['since']})."
                if b
                else f"I had no belief recorded on {as_of}."
            )
        else:
            b = self.belief_now(TOPIC)
            answer = (
                f"Right now I believe: \"{b['belief']}\" (since {b['since']})."
                if b
                else "I have no current belief on that."
            )
        return self._polish(question, answer)

    @staticmethod
    def _extract_date(text: str) -> str | None:
        m = re.search(r"20\d\d-\d\d-\d\d", text)
        return m.group(0) if m else None

    def _polish(self, question: str, draft: str) -> str:
        if not self._llm:
            return draft
        try:
            r = self._llm.generate_content(
                f"Rewrite this agent answer concisely, staying fully faithful to the facts. "
                f"Question: {question}\nFacts: {draft}"
            )
            return r.text.strip()
        except Exception:
            return draft
