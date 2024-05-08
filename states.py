from enum import Enum


class State(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3


class MessageType(Enum):
    ASK_VOTE = 1
    HEARTBEAT = 2
    OK = 3


class LogType(Enum):
    DEFAULT = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
