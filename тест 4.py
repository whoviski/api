import unittest
from app import app, socketio
from flask_testing import TestCase

class TestAPI(TestCase):
    def create_app(self):
        return app

    def test_create_image(self):
        response = self.client.post("/images/", json={"filename": "hello.jpg", "project_id": 111})
        self.assertEqual(response.status_code, 200)
        self.assertIn("upload_link", response.json())

    def test_get_project_images(self):
        response = self.client.get("/projects/111/images")
        self.assertEqual(response.status_code, 200)
