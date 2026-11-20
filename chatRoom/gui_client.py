"""Tkinter chat client.  Usage: python gui_client.py [server_host] [port]"""
import queue
import socket
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 22222


def bring_to_front(win):
    """Apple's Tk 8.5 often opens windows behind everything; force it forward."""
    win.update()
    win.lift()
    win.attributes("-topmost", True)
    win.after(300, lambda: win.attributes("-topmost", False))
    win.focus_force()


class ChatClient:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Chat Room")
        self.win.geometry("500x500+250+150")
        bring_to_front(self.win)
        self.win.configure(bg="#2c3e50")
        self.win.grid_rowconfigure(1, weight=1)
        self.win.grid_columnconfigure(0, weight=1)

        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=self.win)
        if not self.nickname or not self.nickname.strip():
            self.win.destroy()
            return
        self.nickname = self.nickname.strip()

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((HOST, PORT))
        except OSError as e:
            messagebox.showerror("Connection failed", f"Could not connect to {HOST}:{PORT}\n{e}")
            self.win.destroy()
            return

        self.running = True
        self.incoming = queue.Queue()   # network thread -> GUI thread (Tk is not thread-safe)

        label_style = dict(bg="#2c3e50", fg="white", font=("Helvetica", 14, "bold"))
        tk.Label(self.win, text="Chat:", **label_style).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.text_area = scrolledtext.ScrolledText(self.win, state="disabled", wrap="word")
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10)

        tk.Label(self.win, text="Message (/whisper <nick> <msg>, /users):", **label_style).grid(
            row=2, column=0, sticky="w", padx=10, pady=5)

        self.input_area = tk.Text(self.win, height=3)
        self.input_area.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.input_area.bind("<Return>", self.write)   # Shift+Enter still inserts a newline
        self.input_area.focus_set()

        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        threading.Thread(target=self.receive, daemon=True).start()
        self.win.after(100, self.poll_queue)
        self.win.mainloop()

    def write(self, event=None):
        message = self.input_area.get("1.0", "end").strip()
        if message:
            try:
                self.client.sendall((message.replace("\n", " ") + "\n").encode("utf-8"))
            except OSError:
                self.incoming.put("Connection lost.")
        self.input_area.delete("1.0", "end")
        return "break"          # stop Tk from inserting the Enter newline

    def stop(self):
        self.running = False
        try:
            self.client.close()
        except OSError:
            pass
        self.win.destroy()

    def receive(self):
        """Runs in a background thread: only touches the socket and the queue."""
        reader = self.client.makefile("r", encoding="utf-8", errors="replace", newline="\n")
        try:
            for line in reader:
                message = line.rstrip("\n")
                if message == "NICK":
                    self.client.sendall((self.nickname + "\n").encode("utf-8"))
                else:
                    self.incoming.put(message)
        except OSError:
            pass
        if self.running:
            self.incoming.put("Disconnected from server.")

    def poll_queue(self):
        """Runs in the GUI thread: safely appends queued messages."""
        try:
            while True:
                message = self.incoming.get_nowait()
                self.text_area.config(state="normal")
                self.text_area.insert("end", message + "\n")
                self.text_area.yview("end")
                self.text_area.config(state="disabled")
        except queue.Empty:
            pass
        if self.running:
            self.win.after(100, self.poll_queue)


if __name__ == "__main__":
    ChatClient()
