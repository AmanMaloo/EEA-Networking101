# EEA-Networking101
This is the Working Repository for the Project Networking 101 offered in EEA Winter Projects. Please follow the guidelines mentioned while you use the Repository so that we'll not have to revert to previous versions. 

## Setting up the Repository 
- Fork the Repo
-  Create a Branch
-  Clone your forked Repo
-  Commit changes in your branch
-  Pull Changes from the main repo once it's changed
-  get started

## Repository Contents

| Folder | What it covers |
|---|---|
| `Week 1-Python` | Python basics |
| `Week 2-Networking` | Networking fundamentals and socket programming |
| `Week 3 - Web Server` | Building an HTTP web server |
| `Week 4 - TCP,UDP and ICMP` | TCP/UDP servers, SMTP client, ICMP pinger (`icmp_pinger.py`) |
| `Final Showdown/Video Server` | RTSP/RTP video streaming client and server |
| `chatRoom` | Multi-client TCP chat room (details below) |

## Chat Room (`chatRoom/`)

A multi-client chat room over TCP. The server handles each client in its own thread and uses newline-delimited UTF-8 messages, so message boundaries are explicit.

| File | Purpose |
|---|---|
| `server.py` | Chat server, listens on `0.0.0.0:22222` by default |
| `cli_client.py` | Terminal client (main thread sends, receiver thread prints) |
| `gui_client.py` | Tkinter GUI client |
| `chat_entry.py` | GUI launcher: host a room or join someone else's |

