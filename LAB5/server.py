import socket
import threading
import json
import os
import base64

SERVER_MEDIA = "SERVER_MEDIA"
if not os.path.exists(SERVER_MEDIA):
    os.mkdir(SERVER_MEDIA)

clients = []

def format_message(msg_type, payload):
    return json.dumps({"type": msg_type, "payload": payload})

def receive_complete_message(client_socket):
    chunks = []
    while True:
        chunk = client_socket.recv(1)  # receive byte by byte
        if chunk == b'\n':  # message delimiter
            break
        chunks.append(chunk)
    return b''.join(chunks).decode('utf-8')

def handle_client(client_socket, client_address):
    global clients
    print(f"Accepted connection from {client_address}")
    client_name = ""
    client_room = ""

    while True:
        try:
            message_json = receive_complete_message(client_socket)
            if not message_json:
                break

            message_data = json.loads(message_json)
            if message_data["type"] == "connect":
                client_name = message_data["payload"]["name"]
                client_room = message_data["payload"]["room"]
                ack_message = format_message("connect_ack", {"message": "Connected to the room."})
                client_socket.sendall((ack_message + '\n').encode('utf-8'))
                notification = format_message("notification", {"message": f"{client_name} has joined the room."})
                for client in clients:
                    client.sendall((notification + '\n').encode('utf-8'))

            elif message_data["type"] == "exit":
                client_name = message_data["payload"]["name"]
                client_room = message_data["payload"]["room"]
                ack_message = format_message("exit_ack", {"message": "Disconnected to the room."})
                client_socket.sendall((ack_message + '\n').encode('utf-8'))
                notification = format_message("notification", {"message": f"{client_name} has left the room."})
                for client in clients:
                    client.sendall((notification + '\n').encode('utf-8'))

            elif message_data["type"] == "message":
                broadcast_message = format_message("message", {
                    "sender": client_name,
                    "room": client_room,
                    "text": message_data["payload"]["text"]
                })
                for client in clients:
                    client.sendall((broadcast_message + '\n').encode('utf-8'))

            elif message_data["type"] == "upload":
                file_name = message_data["payload"]["file_name"]
                b64_encoded_content = message_data["payload"]["content"]
                file_content = base64.b64decode(b64_encoded_content)
                file_path = os.path.join(SERVER_MEDIA, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                print(f"File {file_name} saved to {file_path}")
                notification = format_message("notification", {"message": f"User {client_name} uploaded the {file_name} file."})
                for client in clients:
                    client.sendall((notification + '\n').encode('utf-8'))

            elif message_data["type"] == "download":
                file_name = message_data["payload"]["file_name"]
                file_path = os.path.join(SERVER_MEDIA, file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    b64_encoded_content = base64.b64encode(file_content).decode('utf-8')
                    send_data = format_message("file", {"file_name": file_name, "content": b64_encoded_content})
                    client_socket.sendall((send_data + '\n').encode('utf-8'))
                else:
                    error_message = format_message("error", {"message": f"The {file_name} doesn't exist."})
                    client_socket.sendall((error_message + '\n').encode('utf-8'))

        except json.JSONDecodeError:
            print(f"Received invalid JSON data from {client_address}. Continuing...")

    clients.remove(client_socket)
    client_socket.close()

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server is listening on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()
