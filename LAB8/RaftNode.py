import socket
import threading
import time
import random
import requests
import json

class RaftNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.state = 'follower'
        self.peers = peers
        self.current_leader = None
        self.last_heartbeat = time.time()
        self.start_election_thread()
        self.follower_credentials = {}
        self.votes_received = 0

    def start_election_thread(self):
        election_thread = threading.Thread(target=self.run_election_cycle)
        election_thread.daemon = True
        election_thread.start()

    def run_election_cycle(self):
        while True:
            time.sleep(self.get_election_timeout())
            if self.state != 'leader':
                self.attempt_to_become_leader()

    # Define the get_election_timeout method
    def get_election_timeout(self):
        return random.uniform(10, 20)

    def attempt_to_become_leader(self):
        for peer in self.peers:
            try:
                response = requests.post(f"http://{peer}/announce_leader", json={'candidate_id': self.node_id})
                if response.status_code == 200 and response.json().get('status') == 'rejected':
                    return  # Another node is already a leader or candidate
            except requests.RequestException:
                pass
        # If no other leader or candidate is found, become the leader
        self.become_leader()

    def become_leader(self):
        self.state = 'leader'
        self.current_leader = self.node_id
        self.send_heartbeats()
        # Update follower list as leader
        for peer in self.peers:
            self.update_follower_list(peer)

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

    def forward_request_to_followers(self, endpoint, data, method):
        if self.state == 'leader':
            for follower in self.follower_credentials.values():
                follower_address = f"{follower['ip']}:{follower['port']}"
                internal_endpoint = '/internal' + endpoint  # Use the internal endpoint
                try:
                    if method == 'POST':
                        requests.post(f"http://{follower_address}{internal_endpoint}", json=data)
                    elif method == 'PUT':
                        requests.put(f"http://{follower_address}{internal_endpoint}", json=data)
                    elif method == 'DELETE':
                        requests.delete(f"http://{follower_address}{internal_endpoint}", json=data)
                except requests.RequestException as e:
                    print(f"Error in {method} request to {follower_address}: {e}")
