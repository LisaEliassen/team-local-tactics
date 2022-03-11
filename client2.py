from client import *

if __name__ == "__main__":
    server = environ.get("SERVER", "localhost")
    client = Client(server)
    client.start()
