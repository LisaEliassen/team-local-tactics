from os import environ
from queue import Queue
from socket import create_connection, timeout

import TLT
from champlistloader import load_some_champs
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
            self._sock.sendall("Ok".encode())
            response = self._sock.recv(self._buffer_size).decode()
            while response != "Both players have joined":
                response = self._sock.recv(self._buffer_size).decode()
            print(response)
            self._playing = True
            #Thread(target=self._recv).start()
            if self._choose_champions():
                pass
            else:
                self._playing = False
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
            if response != "Invalid team" and response != f"Team {player} has already been chosen.":
                return True
        return False

    def _choose_champions(self) -> bool:
        champions = load_some_champs()
        available_champs = TLT.available_champs(champions)
        welcome_msg = '\n' \
                      + 'Welcome to [bold yellow]Team Local Tactics[/bold yellow]!' \
                      + '\n' \
                      + 'Choose two champions.' \
                      + '\n'
        print(welcome_msg)
        print(available_champs)

        while (choice1 := input("Champion choice 1:")).lower() != ".exit":
            if choice1 in champions.keys():
                self._sock.sendall(choice1.encode())

                while (choice2 := input("Champion choice 2:")).lower() != ".exit":
                    if choice2 in champions.keys():
                        self._sock.sendall(choice2.encode())
                        return True
                    else:
                        print("Not a valid champion!")
            else:
                print("Not a valid champion!")

        return False

    def _recv(self):
        while self._playing:
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
