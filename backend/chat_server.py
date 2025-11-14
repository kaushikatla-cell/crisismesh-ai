"""
chat_server.py

Simple TCP chat relay server for the mesh.

- Listens on HOST:PORT
- Any connected client that sends a message gets it relayed to all other clients
"""

import socket
import threading

HOST = "0.0.0.0"
PORT = 9000

clients = []  # list of sockets
clients_lock = threading.Lock()


def broadcast(msg: bytes, sender_sock: socket.socket):
    """Send msg to all clients except the sender."""
    with clients_lock:
        for c in list(clients):
            if c is sender_sock:
                continue
            try:
                c.sendall(msg + b"\n")
            except Exception:
                # Remove client on send failure
                try:
                    clients.remove(c)
                except ValueError:
                    pass
                c.close()


def handle_client(conn: socket.socket, addr):
    print(f"[NEW] connection from {addr}")
    with clients_lock:
        clients.append(conn)

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.strip()
            print(f"[MSG] {addr}: {msg!r}")
            broadcast(msg, conn)
    except Exception as e:
        print(f"[ERROR] client {addr}: {e}")
    finally:
        print(f"[DISCONNECT] {addr}")
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()


def main():
    print(f"[INFO] Starting chat server on {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    main()
