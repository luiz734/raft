
import Pyro5.api
import sys
try:
    nameserver = Pyro5.api.locate_ns()
    leader_uri = nameserver.lookup("leader")
    leader_proxy = Pyro5.api.Proxy(uri=leader_uri)
    print(leader_proxy.update_state(sys.argv[1]))
except Exception as e:
    print(e)
