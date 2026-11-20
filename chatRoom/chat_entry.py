"""Launcher: host a chat room (server + client) or join someone else's."""
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def bring_to_front(win):
    """Apple's Tk 8.5 often opens windows behind everything; force it forward."""
    win.update()
    win.lift()
    win.attributes("-topmost", True)
    win.after(300, lambda: win.attributes("-topmost", False))
    win.focus_force()

def launch_client(host="127.0.0.1"):
    subprocess.Popen([sys.executable, os.path.join(HERE, "gui_client.py"), host], cwd=HERE)


def start_server_gui():
    def run_server():
        import server
        server.start_server()

    threading.Thread(target=run_server, daemon=True).start()
    messagebox.showinfo("Server", "Server started on port 22222. Others can now join.\n"
                                  "Keep this window open to keep the server running.")
    launch_client("127.0.0.1")


def join_gui(root):
    host = simpledialog.askstring("Join", "Server IP address:", initialvalue="127.0.0.1", parent=root)
    if host:
        launch_client(host.strip())


def show_menu():
    root = tk.Tk()
    root.title("Chat Room Entry")
    root.geometry("300x200+200+150")
    bring_to_front(root)
    tk.Label(root, text="Choose an option", font=("Arial", 14)).pack(pady=20)
    tk.Button(root, text="Start a Chat Room", command=start_server_gui, font=("Arial", 12)).pack(pady=10)
    tk.Button(root, text="Join a Chat Room", command=lambda: join_gui(root), font=("Arial", 12)).pack(pady=10)
    root.mainloop()


if __name__ == "__main__":
    show_menu()
