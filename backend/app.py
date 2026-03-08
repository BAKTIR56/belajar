from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://192.168.1.12:8080"

# ========================
# GET USERS
# ========================
@app.route("/users", methods=["GET"])
def get_users():
    r = requests.get(f"{API_URL}/users")
    return jsonify(r.json())


# ========================
# CREATE USER
# ========================
@app.route("/users", methods=["POST"])
def create_user():

    name = request.form.get("name")
    email = request.form.get("email")
    photo = request.files.get("photo")

    if not photo:
        return jsonify({"error": "Photo is required"}), 400

    files = {
        "photo": (photo.filename, photo.stream, photo.content_type)
    }

    data = {
        "name": name,
        "email": email
    }

    r = requests.post(
        f"{API_URL}/users",
        data=data,
        files=files
    )

    return jsonify(r.json()), r.status_code


# ========================
# DELETE USER
# ========================
@app.route("/users/<id>", methods=["DELETE"])
def delete_user(id):

    r = requests.delete(f"{API_URL}/users/{id}")

    return jsonify(r.json()), r.status_code


# ========================
# UPDATE USER
# ========================
@app.route("/users/<id>", methods=["PUT"])
def update_user(id):

    name = request.json.get("name")
    email = request.json.get("email")

    r = requests.put(
        f"{API_URL}/users/{id}",
        json={
            "name": name,
            "email": email
        }
    )

    return jsonify(r.json()), r.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
