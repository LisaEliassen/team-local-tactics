from os import environ
from queue import Queue
from socket import create_connection, timeout
from threading import Thread
from rich import print


class Client:

    def __init__(self, server: str, buffer_size: int = 2048) -> None:
        self._server = server
        self._buffer_size = buffer_size
        self._messages = Queue()
        self._champs = []

    def start(self):
        if self._choose_team():
            self._chatting = True
            Thread(target=self._recv).start()
            self._choose_champions()

    def _choose_champions(self):
        while (message := input("Choose champion:")).lower() != ".exit":
            if message:
                self._sock.sendall(message.encode())
            while not self._messages.empty():
                print(self._messages.get())
        self._chatting = False
        self._sock.close()

    def _choose_team(self) -> bool:
        print("Choosing team...")
        print("Red or Blue? \n")
        while player := input("Player: "):
            message = player
            self._sock = create_connection((self._server, 5550))
            self._sock.sendall(message.encode())
            response = self._sock.recv(self._buffer_size).decode()
            print(response)
            if response != "Invalid team":
                return True
        return False

    def _recv(self):
        while self._chatting:
            try:
                data = self._sock.recv(2048)
            except timeout:
                pass
            except:
                break
            else:
                if data:
                    self._messages.put(data.decode())
                else:
                    break


if __name__ == "__main__":
    server = environ.get("SERVER", "localhost")
    client = Client(server)
    client.start()
