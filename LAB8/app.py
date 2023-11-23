import os

from flask import Flask, request, jsonify, abort
import psycopg2
from flask_swagger_ui import get_swaggerui_blueprint
from RaftNode import RaftNode

app = Flask(__name__)

# Retrieve node ID and peers from environment variables
node_id = os.getenv('NODE_ID')
peers = os.getenv('PEERS', '').split(',')

raft_node = RaftNode(node_id, peers)


def get_db_connection():
    conn = psycopg2.connect(database="scooters",
                            user="admin",
                            password="adminpass",
                            host="db", port="5432")
    return conn


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    if raft_node.state == 'follower':
        leader_id = request.json.get('leader_id')
        raft_node.receive_heartbeat(leader_id)
        # Send back an accept message
        return jsonify({'status': 'accepted', 'follower_id': node_id}), 200
    else:
        return jsonify({'error': 'Invalid state for heartbeat'}), 403

@app.route('/accept_leader', methods=['POST'])
def accept_leader():
    if raft_node.state == 'follower':
        leader_info = request.json  # Extract leader's information
        # Logic to store leader's information
        return jsonify({'status': 'accepted'}), 200
    else:
        return jsonify({'error': 'Not a follower'}), 403

@app.route('/send_credentials', methods=['POST'])
def send_credentials():
    if raft_node.state == 'leader':
        follower_info = request.json
        raft_node.update_follower_list(f"{follower_info['ip']}:{follower_info['port']}")
        return jsonify({'status': 'credentials received'}), 200
    else:
        return jsonify({'error': 'Not the leader'}), 403


@app.route('/scooters/', methods=['GET'])
def list_scooters():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, battery_level FROM scooter")
    scooters = cur.fetchall()
    conn.close()
    return jsonify([{'id': s[0], 'name': s[1], 'battery_level': s[2]} for s in scooters])


@app.route('/scooters/', methods=['POST'])
def create_scooter():
    if raft_node.state != 'leader':
        return jsonify({'error': 'Not the leader'}), 403

    if not request.json or 'name' not in request.json or 'battery_level' not in request.json:
        abort(400)
    name = request.json['name']
    battery_level = request.json['battery_level']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO scooter (name, battery_level) VALUES (%s, %s) RETURNING id", (name, battery_level))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    if raft_node.state == 'leader':
        raft_node.forward_request_to_followers('/scooters/', request.json)

    return jsonify({'id': new_id, 'name': name, 'battery_level': battery_level}), 201


@app.route('/scooters/<int:id>', methods=['GET'])
def get_scooter(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, battery_level FROM scooter WHERE id = %s", (id,))
    scooter = cur.fetchone()
    conn.close()
    if scooter is None:
        abort(404)
    return jsonify({'id': scooter[0], 'name': scooter[1], 'battery_level': scooter[2]})


@app.route('/scooters/<int:id>', methods=['PUT'])
def update_scooter(id):
    if raft_node.state != 'leader':
        return jsonify({'error': 'Not the leader'}), 403

    if not request.json:
        abort(400)
    name = request.json.get('name')
    battery_level = request.json.get('battery_level')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE scooter SET name = %s, battery_level = %s WHERE id = %s", (name, battery_level, id))
    conn.commit()
    conn.close()
    return jsonify({'id': id, 'name': name, 'battery_level': battery_level})


@app.route('/scooters/<int:id>', methods=['DELETE'])
def delete_scooter(id):
    if raft_node.state != 'leader':
        return jsonify({'error': 'Not the leader'}), 403
    password = request.headers.get('X-Delete-Password')
    if password != 'your_secret_password':  # Replace with your actual password
        return jsonify({"error": "Incorrect password"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM scooter WHERE id = %s", (id,))

    if cur.rowcount == 0:  # No rows were deleted, implying scooter was not found.
        conn.close()
        return jsonify({"error": "Electro Scooter not found"}), 404

    conn.commit()
    conn.close()
    return jsonify({"message": "Electro Scooter deleted successfully"}), 200


# Swagger UI setup
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Electro Scooter API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def create_scooter_table_if_not_exists():
    """Create the scooter table if it does not exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if the scooter table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'scooter'
        );
    """)
    table_exists = cur.fetchone()[0]

    # If the table doesn't exist, create it
    if not table_exists:
        cur.execute("""
            CREATE TABLE scooter (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                battery_level INT NOT NULL
            );
        """)
        conn.commit()

    conn.close()


if __name__ == '__main__':
    create_scooter_table_if_not_exists()
    app.run(host='0.0.0.0', debug=True)
