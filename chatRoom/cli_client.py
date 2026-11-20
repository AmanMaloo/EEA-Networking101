"""Terminal chat client.  Usage: python cli_client.py [server_host] [port]"""
import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 22222


def receive(sock, reader, nickname):
    try:
        for line in reader:
            msg = line.rstrip("\n")
            if msg == "NICK":
                sock.sendall((nickname + "\n").encode("utf-8"))
            else:
                print(msg)
    except OSError:
        pass
    print("Disconnected from server.")
    sock.close()


def main():
    nickname = input("Choose a nickname: ").strip() or "anonymous"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except OSError as e:
        print(f"Could not connect to {HOST}:{PORT} - {e}")
        return
    reader = sock.makefile("r", encoding="utf-8", errors="replace", newline="\n")
    threading.Thread(target=receive, args=(sock, reader, nickname), daemon=True).start()

    print("Type a message and press Enter. /whisper <nick> <msg>, /users, /quit")
    try:
        while True:
            text = input().strip()
            if text == "/quit":
                break
            if text:
                # the server adds the sender's nickname itself
                sock.sendall((text + "\n").encode("utf-8"))
    except (EOFError, KeyboardInterrupt, OSError):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()
