from os import environ
from socket import create_server, timeout
from threading import Lock, Thread
from champlistloader import load_some_champs
from rich import print
import TLT as TLT


class ChatServer:

    def __init__(self, host: str, port: int, buffer_size: int = 2048):
        self._host = host
        self._port = port
        self._buffer_size = buffer_size
        self._players = ["Red", "Blue"]
        self._connections = {}
        self._player_lock = Lock()
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

    @property
    def registered_users(self):
        with self._player_lock:
            return list(self._players)

    def _accept(self):
        while self._serving:
            try:
                conn, _ = self._welcome_sock.accept()
            except timeout:
                pass
            else:
                Thread(target=self._welcome, args=(conn,)).start()

    def _welcome(self, conn):
        if data := conn.recv(self._buffer_size):
            player = data.decode()
            if self._choose_team(conn, player):
                with self._connections_lock:
                    self._connections[player] = conn
                while True:
                    if "Blue" in self._connections and "Red" in self._connections:
                        break

                conn.sendall("Both players have joined".encode())
                self._handle_user(conn, player)
        conn.close()

    def _choose_team(self, conn, player):
        with self._player_lock:
            if player in self._players:
                print(f"Player {player} has joined.")
                #conn.sendall("Joined".encode())
                return True
            conn.sendall("Invalid team".encode())
            return False

    def _handle_user(self, conn, player):

        champions = load_some_champs()
        available_champs = TLT.available_champs(champions)
        welcome_msg = '\n' \
                      + 'Welcome to [bold yellow]Team Local Tactics[/bold yellow]!' \
                      + '\n' \
                      + 'Each player choose a champion each time.' \
                      + '\n'

        # TO-DO: Use pickle to convert Rich Table into bit strings:
        #conn.sendall(welcome_msg.encode())
        #conn.sendall(available_champs)

        while self._serving:
            if message := conn.recv(self._buffer_size):
                self._send_from_player(player, message)
            else:
                break
        del self._connections[player]

    def _send_from_player(self, player, message):
        with self._connections_lock:
            for key in self._connections:
                if key != player:
                    try:
                        self._connections[key].sendall(
                            player.encode() + b"| " + message
                        )
                    except:
                        del self._connections[key]


if __name__ == "__main__":
    host = environ.get("HOST", "localhost")
    server = ChatServer(host, 5550)
    server.turn_on()
