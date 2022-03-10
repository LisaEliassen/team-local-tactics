from os import environ
from socket import create_server, timeout
from threading import Lock, Thread
from champlistloader import load_some_champs
from rich import print
import TLT as TLT
import core
import re


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
        self._match_results = {}
        self._match_number = 0

    def turn_on(self):
        self._server_sock = create_server(
            (self._host, self._port)
        )
        self._server_sock.settimeout(5)
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
                conn, _ = self._server_sock.accept()                # establishes connection
            except timeout:
                pass
            else: # because of while loop, "second" time with the same conn value will go to else stmt (instead of try block)
                Thread(target=self._check_client_type, args=(conn,)).start()

    def _check_client_type(self, conn):
        response = conn.recv(self._buffer_size).decode()
        while True:
            #print(response)
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
                self._handle_player(conn, player)

        conn.close()

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
        while self._serving:
            while len(self._champion_choices[player]) < 2:
                if choice := conn.recv(self._buffer_size).decode():
                    self._choose_champions(conn, player, choice)
                else:
                    break
                print(self._champion_choices)

            self._game_result(conn, player)

        del self._connections[player]

    def _get_champions(self):
        self._connections["Database"].sendall("Get champions".encode())

        if champions := self._connections["Database"].recv(self._buffer_size).decode():
            champions = champions.split(',')
            return champions

    def _choose_champions(self, conn, player, choice):
        champions = self._get_champions()
        print(champions)

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

    def _game_result(self, conn, player):
        while len(self._champion_choices[self._get_other_player(player)]) != 2:
            continue

        # use match lock etc
        with self._match_lock:      # SPM til gr.time: betyr dette at lock-en blir acquired i blokken og released etter?
            if str(self._match_number) not in self._match_results.keys():       # for "first" player
                match = TLT.match(self._champion_choices["Red"], self._champion_choices["Blue"])
                self._match_results[self._match_number] = match
            else:                                                               # for "second" player
                match = self._match_results[self._match_number]
                self._match_number += 1

            print(match.rounds)
            TLT.print_match_summary(match)

            self.shut_down()

    def _get_other_player(self, player):
        for key in self._connections:
            if key != player and key != "Database":
                return key

    def _get_data_from_match(self, match):
        pass


if __name__ == "__main__":
    host = environ.get("HOST", "localhost")
    server = Server(host, 5550)
    server.turn_on()
