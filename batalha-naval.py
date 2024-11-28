import socket
import threading
import json
import random
import os
import time


class BattleshipGame:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.board_size = 10
        self.ships = [
            {"type": "Carrier", "size": 5, "symbol": "P"},
            {"type": "Battleship", "size": 4, "symbol": "B"},
            {"type": "Cruiser", "size": 3, "symbol": "C"},
            {"type": "Submarine", "size": 3, "symbol": "S"},
            {"type": "Destroyer", "size": 2, "symbol": "D"},
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
                col = random.randint(0, self.board_size - ship["size"]) if orientation == "H" else random.randint(0, self.board_size - 1)

                if self.can_place_ship(row, col, ship["size"], orientation):
                    self.add_ship(row, col, ship["size"], orientation, ship["symbol"])
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

    def add_ship(self, row, col, size, orientation, symbol):
        for i in range(size):
            if orientation == "H":
                self.my_board[row][col + i] = symbol
            else:
                self.my_board[row + i][col] = symbol

    def display_boards(self):
        print("\nSeu Tabuleiro:")
        self.print_board(self.my_board)
        print("\nTabuleiro do Oponente:")
        self.print_board(self.opponent_board)

    def print_board(self, board):
        # Print column headers
        print("  " + " ".join(str(i) for i in range(self.board_size)))
        for i, row in enumerate(board):
            print(f"{i} " + " ".join(row))

    def handle_turn(self):
        while self.running:
            self.display_boards()
            if self.turn:
                print("Seu turno! Faça um ataque (exemplo: 3 4 para linha 3, coluna 4):")
                try:
                    attack = input("Digite sua jogada (linha coluna): ")
                    row, col = map(int, attack.split())
                    if 0 <= row < self.board_size and 0 <= col < self.board_size:
                        self.connection.sendall(json.dumps({"action": "attack", "row": row, "col": col}).encode())
                        response = json.loads(self.connection.recv(1024).decode())
                        if response["result"] == "hit":
                            print(f"Você acertou o navio em linha {row} coluna {col}!")
                            self.opponent_board[row][col] = "X"
                        elif response["result"] == "miss":
                            print(f"Você errou em linha {row} coluna {col}.")
                            self.opponent_board[row][col] = "O"
                        if response.get("game_over"):
                            print("Você venceu!")
                            self.save_boards()
                            self.end_game("Você venceu! Sair do jogo? [s/n]")
                        self.turn = False
                    else:
                        print("Jogada inválida! Tente novamente.")
                except Exception as e:
                    print("Erro na jogada:", e)
            else:
                print("Aguardando a jogada do oponente...")
                try:
                    data = json.loads(self.connection.recv(1024).decode())
                    if data["action"] == "attack":
                        row, col = data["row"], data["col"]
                        if self.my_board[row][col] in ["P", "B", "C", "S", "D"]:
                            print(f"Seu navio na linha {row} coluna {col} foi destruído pelo oponente!")
                            self.my_board[row][col] = "X"
                            self.connection.sendall(json.dumps({"result": "hit", "game_over": self.check_game_over()}).encode())
                        else:
                            print(f"O oponente errou em linha {row} coluna {col}.")
                            self.connection.sendall(json.dumps({"result": "miss"}).encode())
                        if self.check_game_over():
                            print("Derrota :(")
                            self.save_boards()
                            self.end_game("Derrota :( Sair do jogo? [s/n]")
                        self.turn = True
                except Exception as e:
                    print("Erro ao processar jogada do oponente:", e)
                    self.running = False

    def check_game_over(self):
        for row in self.my_board:
            if any(cell in ["P", "B", "C", "S", "D"] for cell in row):
                return False
        return True

    def save_boards(self):
        with open("tabuleiro_meu.json", "w") as f:
            json.dump(self.my_board, f, indent=4)
        with open("tabuleiro_oponente.json", "w") as f:
            json.dump(self.opponent_board, f, indent=4)

    def end_game(self, message):
        print(message)
        choice = input().lower()
        if choice == "s":
            print("Encerrando o jogo em 5 segundos...")
            time.sleep(5)
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
