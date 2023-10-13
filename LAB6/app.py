from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scooters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Scooter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    battery_level = db.Column(db.Float, nullable=False)

@app.route('/scooters/', methods=['GET'])
def list_scooters():
    scooters = Scooter.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'battery_level': s.battery_level} for s in scooters])

@app.route('/scooters/', methods=['POST'])
def create_scooter():
    if not request.json or 'name' not in request.json or 'battery_level' not in request.json:
        abort(400)
    new_scooter = Scooter(name=request.json['name'], battery_level=request.json['battery_level'])
    db.session.add(new_scooter)
    db.session.commit()
    return jsonify({'id': new_scooter.id, 'name': new_scooter.name, 'battery_level': new_scooter.battery_level}), 201

@app.route('/scooters/<int:id>', methods=['GET'])
def get_scooter(id):
    scooter = Scooter.query.get(id)
    if scooter is None:
        abort(404)
    return jsonify({'id': scooter.id, 'name': scooter.name, 'battery_level': scooter.battery_level})

@app.route('/scooters/<int:id>', methods=['PUT'])
def update_scooter(id):
    scooter = Scooter.query.get(id)
    if scooter is None:
        abort(404)
    if not request.json:
        abort(400)
    scooter.name = request.json.get('name', scooter.name)
    scooter.battery_level = request.json.get('battery_level', scooter.battery_level)
    db.session.commit()
    return jsonify({'id': scooter.id, 'name': scooter.name, 'battery_level': scooter.battery_level})


@app.route('/scooters/<int:id>', methods=['DELETE'])
def delete_scooter(id):
    try:
        # Find the Electro Scooter by ID
        scooter = Scooter.query.get(id)
        if scooter is not None:
            # Get the password from the request headers
            password = request.headers.get('X-Delete-Password')
            # Check if the provided password is correct
            if password == 'your_secret_password':  # Replace with your actual password
                db.session.delete(scooter)
                db.session.commit()
                return jsonify({"message": "Electro Scooter deleted successfully"}), 200
            else:
                return jsonify({"error": "Incorrect password"}), 401
        else:
            return jsonify({"error": "Electro Scooter not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
