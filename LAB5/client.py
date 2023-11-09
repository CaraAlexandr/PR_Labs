import socket
import threading
import json
import os
import uuid
import base64
from datetime import datetime
from colorama import init, Fore
import atexit
import shutil

CLIENT_MEDIA = f"CLIENT_MEDIA_{uuid.uuid4().hex}"
exiting = False

if not os.path.exists(CLIENT_MEDIA):
    os.mkdir(CLIENT_MEDIA)


def cleanup():
    if os.path.exists(CLIENT_MEDIA):
        shutil.rmtree(CLIENT_MEDIA)


atexit.register(cleanup)

init(autoreset=True)


def format_message(msg_type, payload):
    return json.dumps({"type": msg_type, "payload": payload})


def send_complete_message(client_socket, message):
    message += '\n'  # append the delimiter
    client_socket.sendall(message.encode('utf-8'))


def display_message(message_data):
    msg_type = message_data.get("type")
    payload = message_data.get("payload", {})
    timestamp = datetime.now().strftime("%H:%M:%S")

    if msg_type == "connect_ack":
        print(Fore.GREEN + f"[{timestamp}] Server: {payload.get('message')}")
    elif msg_type == "exit_ack":
        print(Fore.GREEN + f"[{timestamp}] Server: {payload.get('message')}")
    elif msg_type == "message":
        sender = payload.get("sender")
        text = payload.get("text")
        print(Fore.BLUE + f"[{timestamp}] {sender}: {text}")
    elif msg_type == "notification":
        print(Fore.GREEN + f"[{timestamp}] Server Notification: {payload.get('message')}")
    elif msg_type == "error":
        print(Fore.RED + f"[{timestamp}] Error: {payload.get('message')}")
    elif msg_type == "file":
        file_name = message_data.get("payload", {}).get("file_name")
        b64_encoded_content = message_data.get("payload", {}).get("content")
        file_content = base64.b64decode(b64_encoded_content)
        with open(os.path.join(CLIENT_MEDIA, file_name), 'wb') as f:
            f.write(file_content)
        print(Fore.YELLOW + f"[{timestamp}] File {file_name} downloaded successfully.")


def receive_messages():
    while True:
        if exiting:
            break
        try:
            # First, read the length of the message
            length_data = client_socket.recv(10).strip()
            if not length_data:
                print("Server closed the connection.")
                break
            message_length = int(length_data)
            chunks = []
            bytes_received = 0
            while bytes_received < message_length:
                chunk = client_socket.recv(min(1024, message_length - bytes_received))
                if not chunk:
                    break
                chunks.append(chunk)
                bytes_received += len(chunk)
            message = b''.join(chunks).decode('utf-8')
            try:
                message_data = json.loads(message)
                display_message(message_data)
            except json.JSONDecodeError:
                print("Received invalid JSON data.")
        except ValueError:
            print("Received invalid message length from server.")
        except ConnectionResetError:
            print("Server closed the connection.")
            break


def send_messages():
    while True:
        message_text = input(Fore.CYAN + "Enter a command: ")

        if message_text.lower().startswith("upload:"):
            file_path = message_text.split(":", 1)[1].strip()
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                file_name = os.path.basename(file_path)
                b64_encoded_content = base64.b64encode(file_content).decode('utf-8')
                message = format_message("upload", {"file_name": file_name, "content": b64_encoded_content})
                send_complete_message(client_socket, message)
            else:
                print(Fore.RED + f"File {file_path} doesn't exist.")

        elif message_text.lower().startswith("download:"):
            file_name = message_text.split(":", 1)[1].strip()
            message = format_message("download", {"file_name": file_name})
            send_complete_message(client_socket, message)

        elif message_text.lower() == 'exit':
            global exiting
            exiting = True
            exit_message = format_message("exit", {"name": client_name, "room": room_name})
            send_complete_message(client_socket, exit_message)
            break


        else:
            message = format_message("message", {"sender": client_name, "room": room_name, "text": message_text})
            send_complete_message(client_socket, message)


def start_client():
    print(Fore.YELLOW + "Welcome to the Chat Client!")
    print(Fore.YELLOW + "Commands: ")
    print(Fore.YELLOW + "1. To upload a file: upload: <path_to_file>")
    print(Fore.YELLOW + "2. To download a file: download: <file_name>")
    print(Fore.YELLOW + "3. To exit: exit")
    print("-" * 50)

    HOST = '127.0.0.1'
    PORT = 12345
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")

    global client_name
    client_name = input("Enter your name: ")
    global room_name
    room_name = input("Enter room name: ")
    connect_message = format_message("connect", {"name": client_name, "room": room_name})
    send_complete_message(client_socket, connect_message)

    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

    send_thread = threading.Thread(target=send_messages)
    send_thread.daemon = True
    send_thread.start()

    send_thread.join()
    receive_thread.join()


if __name__ == "__main__":
    start_client()
