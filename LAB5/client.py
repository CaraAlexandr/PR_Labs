import socket
import threading
import json


def format_message(msg_type, payload):
    return json.dumps({"type": msg_type, "payload": payload})


def display_message(message_data):
    msg_type = message_data.get("type")
    payload = message_data.get("payload", {})

    if msg_type == "connect_ack":
        print(f"Server: {payload.get('message')}")
    elif msg_type == "exit_ack":
        print(f"Server: {payload.get('message')}")
    elif msg_type == "message":
        sender = payload.get("sender")
        text = payload.get("text")
        print(f"{sender}: {text}")
    elif msg_type == "notification":
        print(f"Server Notification: {payload.get('message')}")


def start_client():
    HOST = '127.0.0.1'
    PORT = 12345
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")

    client_name = input("Enter your name: ")
    room_name = input("Enter room name: ")
    connect_message = format_message("connect", {"name": client_name, "room": room_name})
    client_socket.send(connect_message.encode('utf-8'))

    def receive_messages():
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            try:
                message_data = json.loads(message)
                display_message(message_data)
            except json.JSONDecodeError:
                print("Received invalid JSON data.")

    def send_messages():
        while True:
            message_text = input("Enter a message (or 'exit' to quit): ")
            if message_text.lower() == 'exit':
                exit_message = format_message("exit", {"name": client_name, "room": room_name})
                client_socket.send(exit_message.encode('utf-8'))

                client_socket.close()
                break
            message = format_message("message", {"sender": client_name, "room": room_name, "text": message_text})
            client_socket.send(message.encode('utf-8'))

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
