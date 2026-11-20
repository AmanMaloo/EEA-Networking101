"""Multi-client TCP chat server.

Protocol (UTF-8, newline-delimited so TCP message boundaries are explicit):
  server -> client : "NICK"            asks the client for a nickname
  client -> server : "<nickname>"      reply to NICK
  client -> server : "<text>"          broadcast to everyone
  client -> server : "/whisper <nick> <text>"   private message
  client -> server : "/users"          list who is online
"""
import socket
import sys
import threading

HOST = "0.0.0.0"   # listen on all interfaces so other machines can join
PORT = 22222

clients = {}                 # nickname -> socket
clients_lock = threading.Lock()


def safe_send(sock, text):
    """Send one newline-terminated line; return False if the socket is dead."""
    try:
        sock.sendall((text.replace("\n", " ") + "\n").encode("utf-8"))
        return True
    except OSError:
        return False


def broadcast(text):
    with clients_lock:
        targets = list(clients.values())
    for sock in targets:
        safe_send(sock, text)


def remove_client(nick, sock):
    with clients_lock:
        # only remove if this socket still owns the nickname
        if clients.get(nick) is sock:
            del clients[nick]
            removed = True
        else:
            removed = False
    try:
        sock.close()
    except OSError:
        pass
    if removed:
        print(f"{nick} disconnected")
        broadcast(f"{nick} left the chat")


def handle_whisper(sock, nick, message):
    parts = message.split(" ", 2)
    if len(parts) < 3 or not parts[2].strip():
        safe_send(sock, "Usage: /whisper <nickname> <message>")
        return
    _, target_nick, private_msg = parts
    with clients_lock:
        target = clients.get(target_nick)
    if target is None:
        safe_send(sock, f"No user with nickname '{target_nick}' found.")
        return
    safe_send(target, f"[Private] {nick} -> You: {private_msg}")
    safe_send(sock, f"[Private] You -> {target_nick}: {private_msg}")


def handle_client(sock, addr):
    print(f"connected with {addr}")
    reader = sock.makefile("r", encoding="utf-8", errors="replace", newline="\n")
    nick = None
    try:
        # --- handshake: ask for a nickname ---
        if not safe_send(sock, "NICK"):
            return
        requested = reader.readline().strip().replace(" ", "_")
        if not requested:
            return
        with clients_lock:
            nick = requested
            while nick in clients:          # nicknames must be unique (whisper uses them)
                nick += "_"
            clients[nick] = sock
        safe_send(sock, f"connected to chat server as {nick}")
        broadcast(f"{nick} joined the chat")

        # --- main loop: one line == one message ---
        for line in reader:                 # ends when the client disconnects
            message = line.strip()
            if not message:
                continue
            if message.startswith("/whisper"):
                handle_whisper(sock, nick, message)
            elif message == "/users":
                with clients_lock:
                    online = ", ".join(clients)
                safe_send(sock, f"Online: {online}")
            else:
                broadcast(f"{nick} : {message}")
    except (OSError, ValueError):
        pass
    finally:
        if nick is not None:
            remove_client(nick, sock)
        else:
            try:
                sock.close()
            except OSError:
                pass


def start_server(host=HOST, port=PORT):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    print(f"Server is listening on {host}:{port}...")
    while True:
        sock, addr = server.accept()
        threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()


if __name__ == "__main__":
    try:
        start_server(port=int(sys.argv[1]) if len(sys.argv) > 1 else PORT)
    except KeyboardInterrupt:
        print("\nServer stopped.")
