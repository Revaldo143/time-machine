"""Cinematic CLI demo — run this while screen-recording your 3-min video.

    python -m src.demo
"""
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agent import TimeMachineAgent

console = Console()


def say(title: str, body: str, pause: float = 1.2):
    console.print(Panel(body, title=f"[bold cyan]{title}[/]", expand=False))
    time.sleep(pause)


def main():
    agent = TimeMachineAgent().connect()

    console.rule("[bold magenta]TimeMachine — valid-time memory for AI agents[/]")
    console.print("[dim]Graph: timemachine @ FalkorDB | Track 2: Agent Memory & Coordination[/]\n")

    with console.status("[bold green]Querying belief graph..."):
        time.sleep(1.0)

    say("Q1 — today", agent.ask("What caused the checkout outage?"))
    say("Q2 — time travel", agent.ask("What caused the checkout outage?",
                                      as_of="2026-10-08"))
    say("Q3 — further back", agent.ask("What caused the checkout outage?",
                                       as_of="2026-10-05"))
    say("Q4 — why did it change?",
        agent.ask("Why did you change your mind?", as_of="2026-10-10"))
    say("Q5 — what-if time travel",
        agent.ask("What if the traffic report never existed?"))

    table = Table(title="Belief timeline (valid-time edges)")
    table.add_column("Valid from", style="green")
    table.add_column("Valid until", style="yellow")
    table.add_column("Belief", style="white")
    for r in agent.timeline("checkout-outage"):
        table.add_row(r["since"], r["until"] or "now", r["belief"])
    console.print(table)

    console.print(
        "\n[bold]A vector DB can tell you what's similar. "
        "Only a graph can tell you what was true [italic]when[/].[/]"
    )


if __name__ == "__main__":
    main()
