import Pyro5.api

sname = Pyro5.api.locate_ns()
uri = sname.lookup("obj")
object_name = Pyro5.api.Proxy(uri)
print(object_name)
x = object_name.foo()
print(x)
