"""Regression checks for the public student and teacher journeys.

Run with: PYTHONPYCACHEPREFIX=/tmp/dl-pycache python3 -m unittest discover -s tests -v
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TEST_DB = Path(tempfile.gettempdir()) / "discourse-lab-end-to-end-test.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["APP_ENV"] = "development"
os.environ["DB_PATH"] = str(TEST_DB)
os.environ["INITIAL_TEACHER_NAME"] = "Docente QA"
os.environ["INITIAL_TEACHER_EMAIL"] = "docente@example.test"
os.environ["INITIAL_TEACHER_PASSWORD"] = "Clave-de-prueba-123"

from app import create_app  # noqa: E402
from app.infrastructure.database import get_user_progress  # noqa: E402


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def test_student_and_teacher_journeys(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.post("/activities/block1-ej-1/submit", json={}).status_code, 401)

        student = self.app.test_client()
        for path in ("/", "/register", "/login", "/dashboard", "/profile", "/levels/1", "/cuadernillo/view", "/final-project", "/certificate"):
            self.assertEqual(student.get(path, follow_redirects=True).status_code, 200, path)

        response = student.post(
            "/register",
            data={"username": "Estudiante QA", "email": "estudiante@example.test", "password": "Clave-de-prueba-123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(student.get("/activities/block1-ej-1", follow_redirects=True).status_code, 200)

        # A student cannot complete a later activity by calling the API directly.
        self.assertEqual(
            student.post("/activities/block1-ej-15/submit", json={"completed": True, "correct": 1, "score": 100}).status_code,
            403,
        )
        self.assertEqual(
            student.post("/activities/block1-ej-1/submit", json={"completed": False, "score": "incorrecto"}).status_code,
            400,
        )
        completed = student.post(
            "/activities/block1-ej-1/submit",
            json={"completed": True, "correct": 1, "incorrect": 0, "score": 100, "hints_used": 0},
        )
        self.assertEqual(completed.status_code, 200)
        self.assertTrue(completed.get_json()["success"])
        self.assertIn(1, get_user_progress(2))

        student.get("/logout")
        self.assertEqual(
            student.post("/login", data={"email": "estudiante@example.test", "password": "contraseña-mala"}, follow_redirects=True).status_code,
            200,
        )
        self.assertEqual(
            student.post("/login", data={"email": "estudiante@example.test", "password": "Clave-de-prueba-123"}, follow_redirects=True).status_code,
            200,
        )

        teacher = self.app.test_client()
        self.assertEqual(
            teacher.post("/login", data={"email": "docente@example.test", "password": "Clave-de-prueba-123"}, follow_redirects=True).status_code,
            200,
        )
        for path in ("/teacher", "/teacher/students/2", "/teacher/export/csv", "/teacher/export/excel", "/teacher/export/pdf"):
            self.assertEqual(teacher.get(path, follow_redirects=True).status_code, 200, path)
        self.assertEqual(
            teacher.post("/teacher/students/2/notes", data={"body": "Seguimiento de prueba"}, follow_redirects=True).status_code,
            200,
        )

    def test_production_requires_a_secret_key(self):
        environment = {"APP_ENV": "production", "SECRET_KEY": ""}
        with patch.dict(os.environ, environment, clear=False):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
                create_app()


if __name__ == "__main__":
    unittest.main(verbosity=2)
