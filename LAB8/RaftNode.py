import socket
import threading
import time
import random
import requests

class RaftNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.state = 'follower'
        self.peers = peers
        self.current_leader = None
        self.last_heartbeat = time.time()
        self.start_election_thread()
        self.follower_credentials = {}

    def start_election_thread(self):
        election_thread = threading.Thread(target=self.run_election_cycle)
        election_thread.daemon = True
        election_thread.start()

    def run_election_cycle(self):
        while True:
            time.sleep(self.get_election_timeout())
            if self.state != 'leader' and time.time() - self.last_heartbeat > self.get_election_timeout():
                self.start_election()

    def get_election_timeout(self):
        return random.uniform(5, 10)

    def start_election(self):
        self.state = 'candidate'
        election_port = 10000
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            udp_socket.bind(('', election_port))
            self.state = 'leader'
            self.current_leader = self.node_id
            self.send_heartbeats()
        except socket.error:
            self.state = 'follower'
        finally:
            udp_socket.close()

        self.reset_election_timeout()

    def send_heartbeats(self):
        while self.state == 'leader':
            for peer in self.peers:
                try:
                    response = requests.post(f"http://{peer}/heartbeat", json={'leader_id': self.node_id})
                    if response.status_code == 200:
                        self.update_follower_list(peer)
                except requests.RequestException:
                    pass
            time.sleep(self.get_heartbeat_interval())

    def get_heartbeat_interval(self):
        return 15

    def receive_heartbeat(self, leader_id):
        self.current_leader = leader_id
        self.state = 'follower'
        self.last_heartbeat = time.time()

    def reset_election_timeout(self):
        self.last_heartbeat = time.time()

    def update_follower_list(self, follower_address):
        # This method will be called when a heartbeat is successfully sent
        # Assuming follower_address is in the format 'ip:port'
        if follower_address not in self.follower_credentials:
            self.follower_credentials[follower_address] = {'ip': follower_address.split(':')[0],
                                                           'port': follower_address.split(':')[1]}
            print(f"Updated follower list with {follower_address}")

    def forward_request_to_followers(self, endpoint, data):
        if self.state == 'leader':
            for follower in self.follower_credentials.values():
                try:
                    follower_address = f"{follower['ip']}:{follower['port']}"
                    response = requests.post(f"http://{follower_address}{endpoint}", json=data)
                    if response.status_code != 200:
                        print(f"Failed to forward to {follower_address}")
                except requests.RequestException as e:
                    print(f"Error forwarding to {follower_address}: {e}")