from getpass import getpass
from os import environ  # To be discussed in the group session
from queue import Queue
from socket import create_connection, timeout
from threading import Thread


class Client:

    def __init__(self, server: str, buffer_size: int = 2048) -> None:
        self._server = server
        self._buffer_size = buffer_size
        self._messages = Queue()

    def start(self):
        if self._register():
            self._chatting = True
            Thread(target=self._recv).start()
            self._chat()

if __name__ == "__main__":
    server = environ.get("SERVER", "localhost")
    client = Client(server)
    client.start()