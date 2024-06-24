from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///images.db"
app.config["S3_BUCKET"] = "my-bucket"
app.config["S3_ACCESS_KEY"] = "my-access-key"
app.config["S3_SECRET_KEY"] = "my-secret-key"
db = SQLAlchemy(app)
socketio = SocketIO(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(20), default="init")
    versions = db.relationship("ImageVersion", backref="image", lazy=True)

class ImageVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    version = db.Column(db.String(20), nullable=False)
    url = db.Column(db.String(255), nullable=False)

@app.route("/images/", methods=["POST"])
def create_image():
    filename = request.json["filename"]
    project_id = request.json["project_id"]
    image = Image(filename=filename, project_id=project_id)
    db.session.add(image)
    db.session.commit()
    upload_link = f"https://{app.config['S3_BUCKET']}.s3.amazonaws.com/{image.id}/{filename}"
    return jsonify({"upload_link": upload_link, "params": {}})

@app.route("/projects/<int:project_id>/images", methods=["GET"])
def get_project_images(project_id):
    images = Image.query.filter_by(project_id=project_id).all()
    response = []
    for image in images:
        response.append({
            "image_id": image.id,
            "state": image.state,
            "project_id": image.project_id,
            "versions": {
                "original": image.versions.filter_by(version="original").first().url,
                "thumb": image.versions.filter_by(version="thumb").first().url,
                "big_thumb": image.versions.filter_by(version="big_thumb").first().url,
                "big_1920": image.versions.filter_by(version="big_1920").first().url,
                "d2500": image.versions.filter_by(version="d2500").first().url,
            }
        })
    return jsonify({"images": response})

@socketio.on("connect")
def connect(project_id):
    print(f"Client connected to project {project_id}")

@socketio.on("disconnect")
def disconnect():
    print("Client disconnected")

@socketio.on("image_processed")
def image_processed(image_id):
    image = Image.query.get(image_id)
    if image:
        emit("image_updated", {"image_id": image_id, "state": image.state}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app)
