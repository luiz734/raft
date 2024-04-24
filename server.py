import Pyro5.api
from Pyro5.server import expose, oneway

@expose
class Server(object):
    def __init__(self) -> None:
        pass

    # @oneway
    def foo(self):
        print("foo")
        return 2


daemon = Pyro5.api.Daemon()
uri_pyro_objecty = daemon.register(Server)
n_server = Pyro5.api.locate_ns()
n_server.register("obj", uri_pyro_objecty)
daemon.requestLoop()

