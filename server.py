from socket import create_server, timeout
from threading import Lock, Thread
from os import environ


class Server:

    def __init__(self, host: str, port: int, buffer_size: int = 2048):
        self._host = host
        self._port = port
        self._buffer_size = buffer_size
        self._connections = {}
        self._connections_lock = Lock()

    def turn_on(self):
        self._welcome_sock = create_server(
            (self._host, self._port),
            reuse_port=True
        )
        self._welcome_sock.settimeout(5)
        self._serving = True
        Thread(target=self._accept).start()

    def shut_down(self):
        self._serving = False

    @property
    def connected_users(self):
        with self._connections_lock:
            return list(self._connections)


if __name__ == "__main__":
    host = environ.get("HOST", "localhost")
    server = Server(host, 5550)
    server.turn_on()