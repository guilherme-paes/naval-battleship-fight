import socket
import threading
import json
import random

class BattleshipGame:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.board_size = 10
        self.ships = [
            {"type": "Carrier", "size": 5},
            {"type": "Battleship", "size": 4},
            {"type": "Cruiser", "size": 3},
            {"type": "Submarine", "size": 3},
            {"type": "Destroyer", "size": 2}
        ]
        self.my_board = [[" " for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.opponent_board = [[" " for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.turn = False  # False = opponent's turn, True = my turn
        self.running = True
        self.connection = None

    def place_ships(self):
        for ship in self.ships:
            placed = False
            while not placed:
                orientation = random.choice(["H", "V"])
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - 1)

                if self.can_place_ship(row, col, ship["size"], orientation):
                    self.add_ship(row, col, ship["size"], orientation)
                    placed = True

    def can_place_ship(self, row, col, size, orientation):
        if orientation == "H" and col + size > self.board_size:
            return False
        if orientation == "V" and row + size > self.board_size:
            return False

        for i in range(size):
            if orientation == "H" and self.my_board[row][col + i] != " ":
                return False
            if orientation == "V" and self.my_board[row + i][col] != " ":
                return False

        return True

    def add_ship(self, row, col, size, orientation):
        for i in range(size):
            if orientation == "H":
                self.my_board[row][col + i] = "S"
            else:
                self.my_board[row + i][col] = "S"

    def display_boards(self):
        print("\nSeu Tabuleiro:")
        for row in self.my_board:
            print(" ".join(row))
        print("\nTabuleiro do Oponente:")
        for row in self.opponent_board:
            print(" ".join(row))

    def handle_turn(self):
        while self.running:
            if self.turn:
                print("Seu turno! Faça um ataque (exemplo: 3 4 para linha 3, coluna 4):")
                try:
                    attack = input("Digite sua jogada (linha coluna): ")
                    row, col = map(int, attack.split())
                    if 0 <= row < self.board_size and 0 <= col < self.board_size:
                        self.connection.sendall(json.dumps({"action": "attack", "row": row, "col": col}).encode())
                        response = json.loads(self.connection.recv(1024).decode())
                        if response["result"] == "hit":
                            print("Você acertou!")
                            self.opponent_board[row][col] = "X"
                        else:
                            print("Você errou.")
                            self.opponent_board[row][col] = "O"
                        self.turn = False
                except Exception as e:
                    print("Erro na jogada:", e)
            else:
                print("Aguardando a jogada do oponente...")
                try:
                    data = json.loads(self.connection.recv(1024).decode())
                    if data["action"] == "attack":
                        row, col = data["row"], data["col"]
                        if self.my_board[row][col] == "S":
                            print(f"Seu oponente acertou em {row}, {col}!")
                            self.my_board[row][col] = "X"
                            self.connection.sendall(json.dumps({"result": "hit"}).encode())
                        else:
                            print(f"Seu oponente errou em {row}, {col}.")
                            self.connection.sendall(json.dumps({"result": "miss"}).encode())
                        self.turn = True
                except Exception as e:
                    print("Erro ao processar jogada do oponente:", e)
                    self.running = False

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print("Aguardando conexão...")
            self.connection, _ = server_socket.accept()
            print("Conexão estabelecida com o cliente.")
            self.turn = True
            self.handle_turn()

    def start_client(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            self.connection = client_socket
            print("Conexão estabelecida com o servidor.")
            self.handle_turn()

    def start(self):
        self.place_ships()
        self.display_boards()
        mode = input("Digite 's' para servidor ou 'c' para cliente: ").lower()
        if mode == "s":
            self.start_server()
        elif mode == "c":
            self.start_client()


if __name__ == "__main__":
    host = input("Digite o endereço IP do servidor (ou pressione Enter para localhost): ") or "localhost"
    port = 8080
    game = BattleshipGame(host, port)
    game.start()
