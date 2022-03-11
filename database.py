from os import environ
from socket import create_connection, timeout
from champlistloader import load_some_champs
import pickle


class Database:
    def __init__(self, server: str, buffer_size: int = 2048) -> None:
        self._server = server
        self._buffer_size = buffer_size
        self._match_history = {}

    def start(self):
        self._sock = create_connection((self._server, 5550))
        self._sock.sendall("Database".encode())
        self.run_database()

    def run_database(self):
        while True:
            response = self._sock.recv(self._buffer_size).decode()
            match response:
                case "Get champions":
                    self._sock.sendall(self.give_champions().encode())
                case "Get champion info":
                    self._sock.sendall(self.champion_info().encode())
                case "Get match history":
                    continue
                case "Add match to match history":
                    self._sock.sendall("Ready for match".encode())
                    if response_match := pickle.loads(self._sock.recv(self._buffer_size)):
                        self.add_match(response_match)
                case "Get latest match":
                    self._sock.sendall(pickle.dumps(self.get_latest_match()))
                case "Add champion":
                    self._sock.sendall("Ready for new champion".encode())
                    if response_champion := self._sock.recv(self._buffer_size).decode():
                        self.add_champion(response_champion, 'some_champs.txt')
                case "Shut down":
                    self._sock.close()
                    break
                case _:
                    continue

    def champion_info(self) -> str:
        champion_dict = load_some_champs()
        champs_info_string = ""
        for key in champion_dict:
            champion = champion_dict[key]
            champ_string = ','.join(champion.str_tuple)
            champs_info_string = champs_info_string + champ_string + '|'

        return champs_info_string[:-1]

    def give_champions(self) -> str:
        champion_dict = load_some_champs()
        champs_string = ','.join(champion_dict.keys())
        return champs_string

    def add_match(self, match):
        new_key = len(self._match_history.keys()) + 1
        self._match_history[new_key] = match

    def get_latest_match(self):
        return self._match_history[len(self._match_history)]

    def add_champion(self, champion_str, filename):
        with open(filename, 'a') as f:
            f.write('\n'+champion_str)
        f.close()


if __name__ == "__main__":
    server = environ.get("SERVER", "localhost")
    database = Database(server)
    database.start()
