import Pyro5.api
import Pyro5.server
from printer import Printer
import random
import threading
from states import State, MessageType, LogType
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
        self.uri = "PYRO:{peername}@localhost:{port}".format(
            peername=peername, port=port
        )
        self.state = State.FOLLOWER
        self.term = 1
        self.uncommitted_data = ""
        self.data = ""
        self.vote_count = 0
        self.voted_for = ""
        self.heartbeat_timeout_ms = 1000
        self.debug_logs = []
        uris = [
            "PYRO:peer1@localhost:9001",
            "PYRO:peer2@localhost:9002",
            "PYRO:peer3@localhost:9003",
            "PYRO:peer4@localhost:9004",
        ]
        self.all_uris = list(filter(lambda x: x != self.uri, uris))
        # self.debug_log(self.all_uris)

        self.election_timer = Timer(
            self._get_random_election_timer_ms(), self.on_election_timeout
        )
        self.election_timer.start()

        self.heartbeat_timer = Timer(
            self.heartbeat_timeout_ms, self._on_heartbeat_timeout
        )

        # set to true when receiver enough heartbear responses aftera client request
        self.just_got_client_request = False

    # def get_peername(self):
    #     return self.peername

    def _get_random_election_timer_ms(self):
        # return (random.random() * 2.0 + 1.0) * 1000
        return (random.random() * 8.0 + 3.0) * 1000

    # the way clients talk to each other
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
                metadata = {"sender": self.peername, "term": self.term}
                # self.log(LogType.DEFAULT, "Asking " + uri)
                if proxy.on_message_arrived(msg_type, metadata):
                    self.vote_count += 1
            except Exception as e:
                # self.log(LogType.WARNING, "Can't reach" + uri)
                self.log(LogType.WARNING, e)

    def _reply_to_vote_request(self, metadata):
        candidate = metadata["sender"]
        other_term = int(metadata["term"])
        assert candidate and other_term, "Missing required parameters"
        # > or >=??
        if self.voted_for == "" and other_term > int(self.term):
            self.term += 1
            self.voted_for = candidate
            self.log(LogType.DEFAULT, "Voted for " + self.voted_for)
            self.reset_election_timeout()
            return True
        return False

    def reset_election_timeout(self):
        self.election_timer.reset(self._get_random_election_timer_ms())
        self.election_timer.start()

    #  150ms and 300ms
    def on_election_timeout(self) -> None:
        self.term += 1
        self.vote_count = 1
        self.voted_for = self.peername
        self.state = State.CANDIDATE

        self._ask_others_for_vote()
        # maybe check half+1 instead of half
        has_majority_of_votes = self.vote_count > int(TOTAL_PEERS / 2)
        if has_majority_of_votes:
            self._become_leader()
        else:
            self.reset_election_timeout()

    def _become_leader(self) -> None:
        self.log(LogType.SUCCESS, "Leader with " + str(self.vote_count) + " votes")
        nameserver = Pyro5.api.locate_ns()
        nameserver.register("leader", uri)

        self.state = State.LEADER
        self.election_timer.stop()
        self.voted_for = ""
        self.vote_count = 0

        self.heartbeat_timer.reset()
        self.heartbeat_timer.start()

    # The leader begins sending out Append Entries messages to its followers
    def _on_heartbeat_timeout(self) -> None:
        total_acknowledge = 0
        for uri in self.all_uris:
            try:
                proxy = Pyro5.api.Proxy(uri=uri)
                msg_type = MessageType.HEARTBEAT
                # self.log(LogType.DEFAULT, self.uncommitted_data)
                res = proxy.on_message_arrived(
                    msg_type,
                    {
                        "term": self.term,
                        "unc_state": self.uncommitted_data,
                        "state": self.data,
                    },
                )
                if res == MessageType.OK.value:
                    total_acknowledge += 1
            except Exception as _:
                self.log(LogType.WARNING, "Can't send hearbeat to " + uri)
        # >= in this case so it works when 1 peer is down (Acks >= 2 == true)
        enough_heartbeat_acks = total_acknowledge >= int(TOTAL_PEERS / 2)
        # only for debug
        if self.just_got_client_request:
            self.log(LogType.SUCCESS, "Acks " + str(total_acknowledge))
        if self.just_got_client_request and enough_heartbeat_acks:
            self.just_got_client_request = False
            self.commit_state()

        self.heartbeat_timer.reset()
        self.heartbeat_timer.start()

    def reply_to_heartbeat(self, metadata):
        other_term = metadata["term"]
        other_unc_state = metadata["unc_state"]
        other_state = metadata["state"]
        assert other_term != None, "Missing other_term on reply_to_heartbeat"
        assert other_unc_state != None, "Missing other_unc_state on reply_to_heartbeat"
        assert other_state != None, "Missing other_state on reply_to_heartbeat"

        # change to follower when candidate
        self.state = State.FOLLOWER
        # leader send
        self.uncommitted_data = other_unc_state
        self.data = other_state
        self.voted_for = ""
        self.vote_count = 0
        self.reset_election_timeout()
        self.term = other_term
        return MessageType.OK

    def commit_state(self):
        self.data = self.uncommitted_data

    # helpers
    def log(self, log_type, msg):
        self.debug_logs.insert(0, {"log_type": log_type, "msg": str(msg)})

    # client stuff
    def update_state(self, new_state):
        self.just_got_client_request = True
        self.uncommitted_data = new_state
        return True


peer = Peer(cli_peername, cli_port)
printer = Printer(peer)
printer.start()

daemon = Pyro5.api.Daemon(port=int(cli_port))
uri = daemon.register(peer, objectId=cli_peername, weak=True)

t1 = threading.Thread(target=daemon.requestLoop)
t1.start()
