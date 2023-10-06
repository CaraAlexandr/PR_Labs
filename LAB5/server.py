import socket
import threading
import json

clients = []


def format_message(msg_type, payload):
    return json.dumps({"type": msg_type, "payload": payload})


def handle_client(client_socket, client_address):
    global clients
    print(f"Accepted connection from {client_address}")
    client_name = ""
    client_room = ""

    while True:
        try:
            message_json = client_socket.recv(1024).decode('utf-8')
            if not message_json:
                break

            message_data = json.loads(message_json)
            if message_data["type"] == "connect":
                client_name = message_data["payload"]["name"]
                client_room = message_data["payload"]["room"]
                ack_message = format_message("connect_ack", {"message": "Connected to the room."})
                client_socket.send(ack_message.encode('utf-8'))
                notification = format_message("notification", {"message": f"{client_name} has joined the room."})
                for client in clients:
                    client.send(notification.encode('utf-8'))

            if message_data["type"] == "exit":
                client_name = message_data["payload"]["name"]
                client_room = message_data["payload"]["room"]
                ack_message = format_message("exit_ack", {"message": "Disconnected to the room."})
                client_socket.send(ack_message.encode('utf-8'))
                notification = format_message("notification", {"message": f"{client_name} has left the room."})
                for client in clients:
                    client.send(notification.encode('utf-8'))

            elif message_data["type"] == "message":
                broadcast_message = format_message("message", {
                    "sender": client_name,
                    "room": client_room,
                    "text": message_data["payload"]["text"]
                })
                for client in clients:
                    client.send(broadcast_message.encode('utf-8'))

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
