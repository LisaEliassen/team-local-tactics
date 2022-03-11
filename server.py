from os import environ
from socket import create_server, timeout
from threading import Lock, Thread
from rich import print
import TLT as TLT
import pickle


class Server:

    def __init__(self, host: str, port: int, buffer_size: int = 2048):
        self._host = host
        self._port = port
        self._buffer_size = buffer_size
        self._players = ["Red", "Blue"]
        self._player_lock = Lock()
        self._champion_choices = {"Red": [], "Blue": []}
        self._champion_choice_lock = Lock()
        self._connections = {}
        self._connections_lock = Lock()
        self._match_lock = Lock()
        self._match_sem = 0
        self._database_lock = Lock()
        self._players_ready = {"Red": 0, "Blue": 0}

    def turn_on(self):
        self._server_sock = create_server(
            (self._host, self._port)
        )
        self._server_sock.settimeout(5)
        self._serving = True
        Thread(target=self._accept).start()

    def shut_down(self):
        self._serving = False
        self._connections["Database"].sendall("Shut down".encode())
        del self._connections["Database"]
        self._server_sock.close()

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
                conn, _ = self._server_sock.accept()
            except timeout:
                pass
            else:
                Thread(target=self._check_client_type, args=(conn,)).start()

    def _check_client_type(self, conn):
        response = conn.recv(self._buffer_size).decode()
        while True:
            if response == "Player":
                self._player_join(conn)
                break
            elif response == "Database":
                self._database_join(conn)
                break
            else:
                response = conn.recv(self._buffer_size).decode()

    def _database_join(self, conn):
        with self._connections_lock:
            self._connections["Database"] = conn

    def _player_join(self, conn):
        conn.sendall("Choose team".encode())
        if data := conn.recv(self._buffer_size):
            player = data.decode()
            if self._choose_team(conn, player):
                with self._connections_lock:
                    self._connections[player] = conn
                while True:
                    if "Blue" in self._connections and "Red" in self._connections:
                        break
                conn.sendall("Both players have joined".encode())
                while self._serving:
                    self._handle_player(conn, player)
        conn.close()

    def _add_champion(self, champ_str):
        with self._database_lock:
            conn = self._connections["Database"]
            conn.sendall("Add champion".encode())
            response = conn.recv(self._buffer_size).decode()
            while response != "Ready for new champion":
                response = conn.recv(self._buffer_size).decode()
            conn.sendall(champ_str.encode())

    def _choose_team(self, conn, player):
        with self._player_lock:
            if player in self._players:
                if player in self._connections.keys():
                    conn.sendall(f"Team {player} has already been chosen.".encode())
                    return False
                print(f"Player {player} has joined.")
                conn.sendall("Joined".encode())
                response = conn.recv(self._buffer_size).decode()
                while response != "Team chosen":
                    response = conn.recv(self._buffer_size).decode()
                return True
            else:

                conn.sendall("Invalid team".encode())
                return False

    def _handle_player(self, conn, player):
        while True:
            response = conn.recv(self._buffer_size).decode()
            match response:
                case "Play":
                    self._players_ready[player] = 1
                    while True:
                        if self._players_ready["Red"] == 1 and self._players_ready["Blue"] == 1:
                            conn.sendall("Both players are ready".encode())
                            break
                    break
                case "Exit":
                    del self._connections[player]
                    if len(self._connections.keys()) < 2:
                        self.shut_down()
                    break
                case "Add champion":
                    conn.sendall("Ready for new champion".encode())
                    response_champ = conn.recv(self._buffer_size).decode()
                    self._add_champion(response_champ)
                    continue
                case _:
                    continue

        response = conn.recv(self._buffer_size).decode()
        while response != "Get champions":
            response = conn.recv(self._buffer_size).decode()
        conn.sendall(self._get_champion_info().encode())

        while len(self._champion_choices[player]) < 2:
            if choice := conn.recv(self._buffer_size).decode():
                self._choose_champions(conn, player, choice)
            else:
                break

        self._game_result(conn, player)
        self._players_ready[player] = 0
        self._champion_choices[player] = []

    def _choose_champions(self, conn, player, choice):
        champions = self._get_champions()

        valid = False
        for player_key in self._champion_choices:
            if choice in champions:
                if choice not in self._champion_choices[player_key]:
                    valid = True
                else:
                    valid = False
                    break
            else:
                valid = False

        if valid:
            conn.sendall("Valid champion choice".encode())
            with self._champion_choice_lock:
                self._champion_choices[player].append(choice)
        else:
            conn.sendall("Invalid champion choice".encode())

    def _get_match_history(self):
        with self._database_lock:
            self._connections["Database"].sendall("Get match history".encode())

            if match_history := self._connections["Database"].recv(self._buffer_size):
                return pickle.loads(match_history)

    def _send_match(self, match):
        with self._database_lock:
            self._connections["Database"].sendall("Add match to match history".encode())

            response = self._connections["Database"].recv(self._buffer_size).decode()
            while response != "Ready for match":
                response = self._connections["Database"].recv(self._buffer_size).decode()

            self._connections["Database"].sendall(pickle.dumps(match))

    def _get_latest_match(self):
        with self._database_lock:
            self._connections["Database"].sendall("Get latest match".encode())

            if match := self._connections["Database"].recv(self._buffer_size):
                return pickle.loads(match)

    def _game_result(self, conn, player):
        while len(self._champion_choices[self._get_other_player(player)]) != 2:
            continue

        with self._match_lock:

            if self._match_sem == 0:
                champion_info_dict = TLT.champ_string_to_dict(self._get_champion_info())
                match = TLT.match(self._champion_choices["Red"], self._champion_choices["Blue"], champion_info_dict)
                self._send_match(match)
                self._match_sem = 1

            elif self._match_sem == 1:
                match = self._get_latest_match()
                self._match_sem = 0

        conn.sendall("Result ready".encode())
        response = conn.recv(self._buffer_size).decode()
        while response != "Ready for result":
            response = conn.recv(self._buffer_size).decode()
        conn.sendall(pickle.dumps(match))

    def _get_other_player(self, player):
        for key in self._connections:
            if key != player and key != "Database":
                return key

    def _get_champions(self):
        with self._database_lock:
            self._connections["Database"].sendall("Get champions".encode())

            if champions := self._connections["Database"].recv(self._buffer_size).decode():
                champion_list = champions.split(',')
                return champion_list

    def _get_champion_info(self):
        with self._database_lock:
            self._connections["Database"].sendall("Get champion info".encode())

            if champions := self._connections["Database"].recv(self._buffer_size).decode():
                champion_str = champions
                return champion_str


if __name__ == "__main__":
    host = environ.get("HOST", "localhost")
    server = Server(host, 5550)
    server.turn_on()