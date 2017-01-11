from communication.Service import Service
from communication.Client import Client

import threading


# Example implementation of Client/Service Model using RabbitMQ

# Example Service:
#  provides function `fib`
class NumberService(Service):
    def fib(self, n):
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return self.fib(n - 1) + self.fib(n - 2)

# Example Client:
#  skeleton of Service
class NumberClient(Client):
    def fib(self, n):
        return self.call("fib", n)


service = NumberService("fib")


class client_thread(threading.Thread):
    def __init__(self, name, numbers):
        threading.Thread.__init__(self)
        self.name = name
        self.numbers = numbers

    def run(self):
        client = NumberClient("fib")
        for n in self.numbers:
            print(u"[{0:s}] fib({1!r:s}) = {2!r:s}".format(self.name, n, client.fib(n)))


threads = []
for i, r in enumerate([range(12, 20), range(7, 18)]):
    threads.append(client_thread(u"client {0!r:s}".format(i), r))

for t in threads:
    t.start()
for t in threads:
    t.join()

# service.stop()
