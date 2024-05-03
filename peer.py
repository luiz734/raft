import Pyro5.api
import Pyro5.server
from printer import Printer
import random
import threading
import time
from states import State
import sys
from timer import Timer

TOTAL_PEERS = 4

# cli args
cli_peername = sys.argv[1]
cli_port = sys.argv[2]

@Pyro5.api.expose
class Peer:
    def __init__(self, peername, port) -> None:
        self.peername = peername
        self.port = port
        self.state = State.FOLLOWER
        self.term = 0
        self.uncommitted_data = ""
        self.data = ""
        self.vote_count = 0
        self.voted_for = None
        self.heartbeat_timeout_sec = 1
        self.debug_logs = ["started"]


        rand_election_timer = random.random()

        self.election_timer = Timer(2000, self.on_election_timeout)
        self.election_timer.start()

    Pyro5.api.oneway
    def foo(self):
        print("I got something")
        return "bar from " + self.peername
    

    # election stuff
    def ask_others_for_vote(self) -> None:
        pass
    
    def reply_to_vote_request(self, candidate) -> None:
        self.term += 1
        self.voted_for = candidate
        self.reset_election_timeout()
        pass

    def reset_election_timeout(self):
        pass

    #  150ms and 300ms
    def on_election_timeout(self) -> None:
        self.term += 1
        self.vote_count += 1
        self.voted_for = self
        self.state = State.CANDIDATE

        self.ask_others_for_vote()
        has_majority_of_votes = True
        if has_majority_of_votes:
            self.become_leader()
        print("done timeout")

    def become_leader(self) -> None:
        pass

    # The leader begins sending out Append Entries messages to its followers
    def on_heartbeat_timeout(self) -> None:
        pass

    def reply_to_append_entry(self) -> None:
        if self.state != State.FOLLOWER:
            return

    # helpers
    def debug_log(self, msg):
        self.debug_logs.insert(0, msg)

    # client stuff
    def handle_client_request(self, data) -> None:
        if self.state != State.LEADER:
            return
        pass
        self.uncommitted_data = data

    # remaining stuff
    def replicate_uncommitted_data(self) -> None:
        if self.state != State.LEADER:
            return
        # await majority to commit

        majority_confirmed = True
        if majority_confirmed:
            self.data = self.uncommitted_data

    def reply_uncommitted_data(self) -> None:
        if self.state == State.LEADER:
            return

    def replicate_committed_data(self) -> None:
        if self.state != State.LEADER:
            return
        pass

    def reply_committed_data(self) -> None:
        if self.state == State.LEADER:
            return
        self.data = self.uncommitted_data

peer = Peer(cli_peername, cli_port)
printer = Printer(peer)
printer.start()

daemon = Pyro5.api.Daemon(port=int(cli_port))
uri = daemon.register(peer, objectId=cli_peername, weak=True)
print(uri)

t1 = threading.Thread(target=daemon.requestLoop)
t1.start()

uri_string = "PYRO:peer2@localhost:9002"
# try:
proxy = Pyro5.api.Proxy(uri=uri_string)
print(proxy.foo())
# except:



# try:
#     while True:
#         pass
# except KeyboardInterrupt:
#     pass