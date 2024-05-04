import Pyro5.api
import Pyro5.server
from printer import Printer
import random
import threading
import time
from states import State, MessageType
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
        self.uri = "PYRO:{peername}@localhost:{port}".format(peername=peername, port=port)
        self.state = State.FOLLOWER
        self.term = 1
        self.uncommitted_data = ""
        self.data = ""
        self.vote_count = 0
        self.voted_for = ""
        self.heartbeat_timeout_ms = 1000
        self.debug_logs = ["started"]
        uris = [
            "PYRO:peer1@localhost:9001",
            "PYRO:peer2@localhost:9002",
            "PYRO:peer3@localhost:9003",
            "PYRO:peer4@localhost:9004"
        ]
        self.all_uris = list(filter(lambda x: x != self.uri, uris))
        print(self.all_uris)


        self.election_timer = Timer(self._get_random_election_timer_ms(),
                                    self.on_election_timeout)
        self.election_timer.start()

        self.heartbeat_timer = Timer(self.heartbeat_timeout_ms,
                                    self._on_heartbeat_timeout)


    # def get_peername(self):
    #     return self.peername
    
    def _get_random_election_timer_ms(self):
        return (random.random() * 8.0 + 3.0) * 1000
    
    def on_message_arrived(self, msg_type, metadata):
        assert metadata != None and msg_type, "Missing required parameters"

        if msg_type == MessageType.ASK_VOTE.value:
            return self._reply_to_vote_request(metadata)
        elif msg_type == MessageType.HEARTBEAT.value:
            return self.reply_to_heartbeat(metadata)

    # election stuff
    def _ask_others_for_vote(self) -> None:
        for uri in self.all_uris:
            try:
                proxy = Pyro5.api.Proxy(uri=uri)
                msg_type = MessageType.ASK_VOTE
                metadata = {
                        "sender": self.peername,
                        "term": self.term
                        }
                print("asking to " + uri)
                if proxy.on_message_arrived(msg_type, metadata):
                    self.vote_count += 1
            except Exception as e:
                print("Cant reach " + uri)
                print(e)

    def _reply_to_vote_request(self, metadata):
        candidate = metadata["sender"]
        other_term = int(metadata["term"])
        assert candidate and other_term, "Missing required parameters"
        print("voted for: ", self.voted_for)
        # > or >=??
        if self.voted_for == "" and other_term > int(self.term):
            self.term += 1
            self.voted_for = candidate
            self.reset_election_timeout()
            return True
        return False

    def reset_election_timeout(self):
        pass

    #  150ms and 300ms
    def on_election_timeout(self) -> None:
        self.term += 1
        self.vote_count += 1
        self.voted_for = self.peername
        self.state = State.CANDIDATE

        self._ask_others_for_vote()
        has_majority_of_votes = self.vote_count > int(TOTAL_PEERS / 2)
        if self.term > 1:
            print(has_majority_of_votes)
        if has_majority_of_votes:
            self._become_leader()
        else:
            self.election_timer.reset(self._get_random_election_timer_ms())

    def _become_leader(self) -> None:
        self.state = State.LEADER
        self.election_timer.stop()
        self.voted_for = ""
        self.vote_count = 0

        self.heartbeat_timer.reset()
        self.heartbeat_timer.start()


    # The leader begins sending out Append Entries messages to its followers
    def _on_heartbeat_timeout(self) -> None:
        for uri in self.all_uris:
            try:
                proxy = Pyro5.api.Proxy(uri=uri)
                msg_type = MessageType.HEARTBEAT
                res = proxy.on_message_arrived(msg_type, {"term": self.term})
                if res != MessageType.OK.value:
                    print("follower return bad stuff")
            except Exception as e:
                print("Cant send hearbeat to " + uri)
                print(e)
        self.heartbeat_timer.reset()
        self.heartbeat_timer.start()

    def reply_to_heartbeat(self, metadata):
        other_term = metadata["term"]
        assert other_term, "Missing other term on reply_to_heartbeat"
        self.state = State.FOLLOWER
        self.voted_for = ""
        self.vote_count = 0
        self.election_timer.reset(self._get_random_election_timer_ms())
        self.election_timer.start()
        self.term = other_term
        return MessageType.OK

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
# t1.join()

# try:
#     while True:
#         pass
# except KeyboardInterrupt:
#     pass
