import socket
import threading
import json
import random
import os


class Peer:
    def __init__(self, is_server, host, port=8080):
        self.is_server = is_server
        self.host = host
        self.port = port
        self.connection = None
        self.board = [[" " for _ in range(10)] for _ in range(10)]
        self.opponent_board = [[" " for _ in range(10)] for _ in range(10)]
        self.ships = self.place_ships_randomly()
        self.turn = False

    def place_ships_randomly(self):
        ships = [
            ("C", 3),  # Cruiser
            ("D", 2),  # Destroyer
            ("P", 5),  # Aircraft Carrier
            ("E", 4),  # Battleship
        ]
        board = [[" " for _ in range(10)] for _ in range(10)]
        for ship, size in ships:
            placed = False
            while not placed:
                direction = random.choice(["H", "V"])  # Horizontal or Vertical
                row = random.randint(0, 9)
                col = random.randint(0, 9)
                if direction == "H" and col + size <= 10:
                    if all(board[row][col + i] == " " for i in range(size)):
                        for i in range(size):
                            board[row][col + i] = ship
                        placed = True
                elif direction == "V" and row + size <= 10:
                    if all(board[row + i][col] == " " for i in range(size)):
                        for i in range(size):
                            board[row + i][col] = ship
                        placed = True
        return board

    def display_boards(self):
        print("\nSeu Tabuleiro:")
        for row in self.board:
            print(" ".join(row))
        print("\nTabuleiro do Oponente:")
        for row in self.opponent_board:
            print(" ".join(row))

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        print(f"Servidor aguardando conexão em {self.host}:{self.port}...")
        self.connection, _ = server_socket.accept()
        print("Cliente conectado!")
        self.handle_game()

    def start_client(self):
        while True:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(f"Tentando conectar a {self.host}:{self.port}...")
                client_socket.connect((self.host, self.port))
                self.connection = client_socket
                print("Conectado ao servidor!")
                self.handle_game()
                break
            except (socket.error, OSError) as e:
                print(f"Erro ao conectar: {e}")
                retry = input("Tentar novamente? (s/n): ").strip().lower()
                if retry != "s":
                    print("Saindo do cliente.")
                    return

    def handle_game(self):
        self.display_boards()
        # Lógica de jogo: persiste até o final
        while True:
            if self.is_server and self.turn:
                print("Seu turno!")
                move = input("Digite a jogada (linha e coluna): ")
                self.connection.send(move.encode())
                result = self.connection.recv(1024).decode()
                print(f"Resultado: {result}")
            elif not self.is_server and not self.turn:
                print("Aguardando turno do oponente...")
                move = self.connection.recv(1024).decode()
                print(f"Oponente jogou: {move}")
                result = "Acertou!" if move in self.ships else "Errou!"
                self.connection.send(result.encode())
            else:
                print("Esperando...")

    def start(self):
        if self.is_server:
            self.start_server()
        else:
            self.start_client()


if __name__ == "__main__":
    mode = input("Iniciar como servidor (s) ou cliente (c)? ").strip().lower()
    if mode == "s":
        peer = Peer(is_server=True, host="0.0.0.0")
    elif mode == "c":
        server_ip = input("Digite o endereço IP do servidor (ou pressione Enter para localhost): ").strip() or "localhost"
        peer = Peer(is_server=False, host=server_ip)
    else:
        print("Opção inválida. Encerrando o programa.")
        exit(1)

    peer.start()
