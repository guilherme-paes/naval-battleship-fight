import socket
import threading
import json
import random

class BattleshipGame:
    def __init__(self):
        self.board_size = 10
        self.my_board = [[" " for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.opponent_board = [[" " for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.ships = self.generate_ships()
        self.place_ships_randomly()
        self.game_running = True
        self.turn = False  # True for your turn, False for opponent's turn

    def generate_ships(self):
        return {
            "porta-avioes": 5,
            "encouracado": 4,
            "cruzador": 3,
            "destroier": 2
        }

    def place_ships_randomly(self):
        for ship, size in self.ships.items():
            placed = False
            while not placed:
                direction = random.choice(["H", "V"])
                row, col = random.randint(0, 9), random.randint(0, 9)
                if self.can_place_ship(row, col, size, direction):
                    self.place_ship(row, col, size, direction, ship[0].upper())
                    placed = True

    def can_place_ship(self, row, col, size, direction):
        if direction == "H" and col + size > self.board_size:
            return False
        if direction == "V" and row + size > self.board_size:
            return False
        for i in range(size):
            r, c = (row + i, col) if direction == "V" else (row, col + i)
            if self.my_board[r][c] != " ":
                return False
        return True

    def place_ship(self, row, col, size, direction, symbol):
        for i in range(size):
            r, c = (row + i, col) if direction == "V" else (row, col + i)
            self.my_board[r][c] = symbol

    def print_boards(self):
        print("\nSeu Tabuleiro:")
        for row in self.my_board:
            print(" ".join(row))
        print("\nTabuleiro do Oponente:")
        for row in self.opponent_board:
            print(" ".join(row))


class Peer:
    def __init__(self, is_server, host="localhost", port=8080):
        self.is_server = is_server
        self.host = host
        self.port = port
        self.game = BattleshipGame()
        self.connection = None

    def start(self):
        if self.is_server:
            self.start_server()
        else:
            self.start_client()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        print("Servidor aguardando conexão...")
        self.connection, _ = server_socket.accept()
        print("Cliente conectado!")
        self.handle_game()

    def start_client(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Tentando conectar ao servidor...")
        client_socket.connect((self.host, self.port))
        print("Conectado ao servidor!")
        self.connection = client_socket
        self.handle_game()

    def handle_game(self):
        threading.Thread(target=self.receive_data).start()
        while self.game.game_running:
            if self.game.turn:
                self.play_turn()

    def receive_data(self):
        while self.game.game_running:
            try:
                data = self.connection.recv(1024).decode()
                if data:
                    self.process_received_data(data)
            except ConnectionResetError:
                print("Conexão perdida!")
                self.game.game_running = False

    def send_data(self, data):
        json_data = json.dumps(data)
        self.connection.sendall(json_data.encode())

    def process_received_data(self, data):
        data = json.loads(data)
        if "attack" in data:
            result = self.process_attack(data["attack"])
            self.send_data(result)
            self.game.turn = True
        elif "result" in data:
            print(f"Resultado do ataque: {data['result']}")
            self.game.turn = False

    def process_attack(self, attack):
        row, col = map(int, attack)
        if self.game.my_board[row][col] != " ":
            self.game.my_board[row][col] = "X"
            return {"result": "hit"}
        else:
            self.game.my_board[row][col] = "O"
            return {"result": "miss"}

    def play_turn(self):
        self.game.print_boards()
        move = input("Informe as coordenadas para ataque (ex: 23): ")
        self.send_data({"attack": move})
        self.game.turn = False


if __name__ == "__main__":
    mode = input("Iniciar como servidor (s) ou cliente (c)? ").lower()
    is_server = mode == "s"
    peer = Peer(is_server)
    peer.start()
