from os import environ
from socket import create_connection, timeout
from champlistloader import load_some_champs


class Database:
    def __init__(self, server: str, buffer_size: int = 2048) -> None:
        self._server = server
        self._buffer_size = buffer_size

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
                    pass
                case "":
                    pass
                case _:
                    continue

    def champion_info(self) -> str:
        champion_dict = load_some_champs()
        champs_info_string = ""
        for key in champion_dict:
            champion = champion_dict[key]
            champ_string = ','.join(champion.str_tuple)
            champs_info_string = champs_info_string + champ_string + ','

        return champs_info_string

    def give_champions(self) -> str:
        champion_dict = load_some_champs()
        champs_string = ','.join(champion_dict.keys())
        return champs_string

if __name__ == "__main__":
    server = environ.get("SERVER", "localhost")
    database = Database(server)
    database.start()
