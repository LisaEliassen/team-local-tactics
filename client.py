from os import environ
from socket import create_connection
from rich import print
import TLT
import pickle


class Client:

    def __init__(self, server: str, buffer_size: int = 2048) -> None:
        self._server = server
        self._buffer_size = buffer_size
        self._champs = []

    def start(self):
        if self._choose_team():
            self._sock.sendall("Team chosen".encode())
            response = self._sock.recv(self._buffer_size).decode()
            while response != "Both players have joined":
                response = self._sock.recv(self._buffer_size).decode()
            print(response)

            self._playing = True

            while self._playing:
                self._lobby()

                if self._playing == False:
                    break

                response = self._sock.recv(self._buffer_size).decode()
                while response != "Both players are ready":
                    response = self._sock.recv(self._buffer_size).decode()

                #self._playing = True
                if self._choose_champions():
                    self._game_result()
                else:
                    self._playing = False
            self._sock.close()

    def _lobby(self):
        print("\nType 'Play' to play, 'Exit' to exit and 'Add champion' to add a champion.\n")
        while choice := input("> "):
            match choice:
                case "Play":
                    self._sock.sendall("Play".encode())
                    break
                case "Exit":
                    self._sock.sendall("Exit".encode())
                    self._playing = False
                    break
                case "Add champion":
                    self._sock.sendall("Add champion".encode())
                    response = self._sock.recv(self._buffer_size).decode()
                    while response != "Ready for new champion":
                        response = self._sock.recv(self._buffer_size).decode()

                    champion = input("Champion name: ")
                    while True:
                        try:
                            stat1 = int(input("Champion stat 1: "))
                            champion += ',' + str(stat1)
                            break
                        except:
                            print("Invalid format. Try again.")
                    while True:
                        try:
                            stat2 = int(input("Champion stat 2: "))
                            champion += ',' + str(stat2)
                            break
                        except:
                            print("Invalid format. Try again.")
                    while True:
                        try:
                            stat3 = int(input("Champion stat 3: "))
                            champion += ',' + str(stat3)
                            break
                        except:
                            print("Invalid format. Try again.")

                    self._sock.sendall(champion.encode())
                    print("Champion added!")

                case _:
                    continue

    def _choose_team(self) -> bool:
        print("Choosing team...")
        print("Red or Blue? \n")
        while player := input("Player: "):
            self._sock = create_connection((self._server, 5550))
            self._sock.sendall("Player".encode())

            response = self._sock.recv(self._buffer_size).decode()
            while response != "Choose team":
                response = self._sock.recv(self._buffer_size).decode()

            player_choice = player
            self._sock.sendall(player_choice.encode())
            response = self._sock.recv(self._buffer_size).decode()
            print(response)
            if response != "Invalid team" and response != f"Team {player} has already been chosen.":
                return True
        return False

    def _choose_champions(self) -> bool:
        self._sock.sendall("Get champions".encode())
        if response := self._sock.recv(self._buffer_size).decode():
            champions = response

        champions = TLT.champ_string_to_dict(champions)
        available_champs = TLT.available_champs(champions)
        welcome_msg = '\n' \
                      + 'Welcome to [bold yellow]Team Local Tactics[/bold yellow]!' \
                      + '\n' \
                      + 'Choose two champions.' \
                      + '\n'
        print(welcome_msg)
        print(available_champs)

        # CHAMPION CHOICE 1:
        while (choice1 := input("Champion choice 1 of 2:")).lower() != ".exit":
            self._sock.sendall(choice1.encode())
            response = self._sock.recv(self._buffer_size).decode()
            if response == "Valid champion choice":

                # CHAMPION CHOICE 2:
                while (choice2 := input("Champion choice 2 of 2:")).lower() != ".exit":
                    self._sock.sendall(choice2.encode())
                    response = self._sock.recv(self._buffer_size).decode()
                    if response == "Valid champion choice":
                        return True
                    elif response == "Invalid champion choice":
                        print("Invalid champion or champion is already taken.")
                return False

            elif response == "Invalid champion choice":
                print("Invalid champion or champion is already taken.")
        return False

    def _game_result(self):
        response = self._sock.recv(self._buffer_size).decode()
        while response != "Result ready":
            response = self._sock.recv(self._buffer_size).decode()
        self._sock.sendall("Ready for result".encode())
        if response := self._sock.recv(self._buffer_size):
            match = pickle.loads(response)

        print(f"\nMATCH RESULTS:\n")
        TLT.print_match_summary(match)

        """
        self._sock.sendall("Ready to shut down".encode())
        self._sock.close()
        """

if __name__ == "__main__":
    server = environ.get("SERVER", "localhost")
    client = Client(server)
    client.start()
