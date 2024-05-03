import threading
import random
from rich.console import Console
from rich.live import Live
from rich.table import Table
import time
from states import State

class Printer:
    def __init__(self, peer, interval_sec=1) -> None:
        self.peer = peer
        self.paused = False
        self.interval_sec = interval_sec
        self.max_entries = 5

    def start(self):
        t = threading.Thread(target=self.loop_print, daemon=True)
        t.start()

    def loop_print(self) -> None:
        with Live(self.print(), refresh_per_second=60, transient=False) as live:  # update 4 times a second to feel fluid
            while True:
                live.update(self.print())

    def print(self) -> Table:
        # self.console.clear()
        # self.console = Console()
        p = self.peer
        t = Table(show_header=False, title="Peer State", expand=True, show_lines=False, show_edge=True, box=None)
        t.add_column(min_width=10, max_width=10, ratio=2, style="dim")
        t.add_column(ratio=6)

        t.add_row("peer", p.peername)
        t.add_row("port", p.port)
        t.add_row("state", self._get_state_formated())
        t.add_row("term", str(p.term))
        t.add_row("vote_count", str(p.vote_count))
        t.add_row("voted_for", self._get_voted_for())
        t.add_row("election", str(p.election_timer.remaining_sec()))

        t.add_row("[red]uncommitted[/]", p.uncommitted_data)
        t.add_row("[green]committed[/]", p.data)

        return t
        self.console.print(t)
        self.console.rule()
        start = 0
        end = min(len(p.debug_logs), self.max_entries)
        index = start
        while index < end:
            self.console.log(p.debug_logs[index])
            index += 1


    def _get_voted_for(self):
        if self.peer.voted_for:
            return self.peer.voted_for.peername
        else:
            return "None"
    def _get_state_formated(self):
        match self.peer.state:
            case State.FOLLOWER:
                return "" + str(self.peer.state) #+ "[/]"
            case State.CANDIDATE:
                return "[yellow]" + str(self.peer.state) + "[/]"
            case State.LEADER:
                return "[green]" + str(self.peer.state) + "[/]"

