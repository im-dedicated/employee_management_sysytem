import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, init_db


class EmployeeManagementSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_employees.db")
        app.config.update(TESTING=True, DATABASE=self.db_path)
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Employee Management System", response.data)

    def test_registration_and_login_flow(self):
        register_response = self.client.post(
            "/register",
            data={
                "username": "demo",
                "email": "demo@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
            follow_redirects=True,
        )
        self.assertEqual(register_response.status_code, 200)

        login_response = self.client.post(
            "/login",
            data={"username": "demo", "password": "secret123"},
            follow_redirects=True,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b"Welcome back!", login_response.data)

    def test_employee_can_be_edited(self):
        self.client.post(
            "/register",
            data={
                "username": "editor",
                "email": "editor@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"username": "editor", "password": "secret123"},
            follow_redirects=True,
        )

        self.client.post(
            "/employees",
            data={
                "full_name": "John Doe",
                "role": "Developer",
                "department": "Engineering",
                "email": "john@example.com",
                "phone": "12345",
            },
            follow_redirects=True,
        )

        edit_response = self.client.post(
            "/employees/1/edit",
            data={
                "full_name": "John Smith",
                "role": "Senior Developer",
                "department": "Platform",
                "email": "john.smith@example.com",
                "phone": "54321",
            },
            follow_redirects=True,
        )

        self.assertEqual(edit_response.status_code, 200)
        self.assertIn(b"John Smith", edit_response.data)
        self.assertIn(b"Senior Developer", edit_response.data)


if __name__ == "__main__":
    unittest.main()
