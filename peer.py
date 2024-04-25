import Pyro5.api
from Pyro5.server import expose, oneway, threading
import sys

peer_name = sys.argv[1]
port = sys.argv[2]

print("peer_name: ", peer_name)
print("port: ", port)

@expose
class Peer(object):
    def __init__(self) -> None:
        pass

    # @oneway
    def foo(self, msg):
        print("new message: ", msg)
        return 2


daemon = Pyro5.api.Daemon(port=int(port))
uri_pyro_objecty = daemon.register(Peer, objectId=peer_name)
print(uri_pyro_objecty)
# n_server = Pyro5.api.locate_ns()
# n_server.register("obj", uri_pyro_objecty)
t1 = threading.Thread(target=daemon.requestLoop)
t1.start()
# t1.join()
# daemon.requestLoop()
print("foo")

if port == "9001":
    # uri_string = "PYRO:peer2@localhost:9002"
    pass
else:
    uri_string = "PYRO:peer1@localhost:9001"
    object_name = Pyro5.api.Proxy(uri=uri_string)
    x = object_name.foo("hello from " + peer_name)

