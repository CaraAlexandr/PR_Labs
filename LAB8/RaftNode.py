import socket
import threading
import time
import random
import requests
import os


class RaftNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.state = 'follower'
        self.peers = peers.split(',') if isinstance(peers, str) else peers
        self.current_leader = None
        self.udp_port = 10000  # Example port for UDP leader election
        self.http_port = os.getenv('EXTERNAL_PORT', '5000')  # HTTP port from environment variable
        self.start_udp_server()
        self.term = 0
        self.voted_for = None
        self.votes_received = 0

    def start_udp_server(self):
        election_thread = threading.Thread(target=self.run_election_cycle)
        election_thread.daemon = True
        election_thread.start()

    def run_election_cycle(self):
        while True:
            time.sleep(self.get_election_timeout())
            if self.state != 'leader':
                self.start_election()

    def start_election(self):
        self.state = 'candidate'
        self.term += 1
        self.voted_for = self.node_id
        votes_received = 1  # Vote for self
        for peer in self.peers:
            self.request_vote(peer)

    def request_vote(self, peer):
        try:
            response = requests.post(f"http://{peer}/request_vote", json={
                'candidate_id': self.node_id,
                'term': self.term
            })
            if response.status_code == 200 and response.json().get('vote_granted'):
                self.votes_received += 1
                if self.votes_received > len(self.peers) // 2:
                    self.become_leader()
        except requests.RequestException as e:
            print(f"Error requesting vote from {peer}: {e}")

    def become_leader(self):
        self.state = 'leader'
        self.current_leader = self.node_id
        print(f"{self.node_id} has become the leader")
        self.send_heartbeats()

    def handle_vote_request(self, candidate_id, term):
        if self.term < term and (self.voted_for is None or self.voted_for == candidate_id):
            self.voted_for = candidate_id
            self.term = term
            self.reset_election_timeout()
            return True
        return False

    def get_election_timeout(self):
        return random.uniform(10, 20)

    def attempt_to_become_leader(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.udp_socket.bind(('0.0.0.0', self.udp_port))
            self.state = 'leader'
            self.current_leader = self.node_id
            print(f"{self.node_id} became the leader")
            self.send_heartbeats()
        except socket.error:
            self.state = 'follower'
            print(f"{self.node_id} is a follower")
            self.udp_socket.close()

    def send_heartbeats(self):
        """Send regular heartbeats to followers."""
        while self.state == 'leader':
            for peer in self.peers:
                try:
                    response = requests.post(f"http://{peer}/heartbeat", json={'leader_id': self.node_id})
                    if response.status_code != 200:
                        print(f"Failed to send heartbeat to {peer}")
                except requests.RequestException as e:
                    print(f"Error sending heartbeat to {peer}: {e}")
            time.sleep(self.get_heartbeat_interval())

    def get_heartbeat_interval(self):
        """Get the interval at which to send heartbeats."""
        return 5  # Interval in seconds, adjust as needed
    def receive_heartbeat(self, leader_id):
        """Receive a heartbeat from the leader."""
        self.current_leader = leader_id
        # Reset the election timeout since a valid heartbeat is received
        self.reset_election_timeout()
        # Ensure the node remains in follower state
        self.state = 'follower'
        print(f"Heartbeat received from leader {leader_id}")

    def reset_election_timeout(self):
        """Reset the election timeout."""
        self.last_heartbeat = time.time()
        print("Election timeout reset")
    def get_heartbeat_interval(self):
        return 15

    def forward_request_to_followers(self, endpoint, data, method):
        if self.state == 'leader':
            for follower in self.peers:
                try:
                    url = f"http://{follower}{endpoint}"
                    if method == 'POST':
                        requests.post(url, json=data)
                    elif method == 'PUT':
                        requests.put(url, json=data)
                    elif method == 'DELETE':
                        requests.delete(url, json=data)
                except requests.RequestException as e:
                    print(f"Error forwarding {method} request to {follower}: {e}")

    def send_accept_message_to_leader(self, leader_ip):
        """Send an accept message to the leader."""
        if self.state == 'follower':
            try:
                response = requests.post(f"http://{leader_ip}/accept_leader", json={'follower_id': self.node_id,
                                                                                    'follower_ip': f'{socket.gethostname()}:{self.http_port}'})
                if response.status_code == 200:
                    self.receive_leader_credentials(response.json())
            except requests.RequestException as e:
                print(f"Error sending accept message to leader: {e}")

    def receive_leader_credentials(self, leader_info):
        """Receive and store leader's HTTP credentials."""
        if self.state == 'follower':
            # Store leader's credentials for future communication
            self.leader_credentials = leader_info
            print(f"Received leader credentials: {leader_info}")

    def handle_accept_message(self, follower_info):
        """Handle accept message from a follower."""
        if self.state == 'leader':
            # Store follower's info for forwarding requests
            self.follower_credentials[follower_info['follower_id']] = follower_info
            self.send_credentials_to_follower(follower_info['follower_id'], follower_info['follower_ip'])

    def send_credentials_to_follower(self, follower_id, follower_ip):
        """Send leader's HTTP credentials to follower."""
        try:
            leader_info = {'leader_id': self.node_id, 'leader_ip': f'{socket.gethostname()}:{self.http_port}'}
            response = requests.post(f"http://{follower_ip}/send_credentials", json=leader_info)
            if response.status_code == 200:
                print(f"Sent credentials to follower {follower_id}")
        except requests.RequestException as e:
            print(f"Error sending credentials to follower {follower_id}: {e}")
