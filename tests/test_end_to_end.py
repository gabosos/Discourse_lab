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
from app.infrastructure.database import get_user_progress, get_activity_progress, get_route_mode, get_user_by_email, get_activities_by_level  # noqa: E402


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def test_student_and_teacher_journeys(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.post("/activities/block1-ej-1/submit", json={}).status_code, 401)
        activity_types = {activity["activity_type"] for level_id in range(1, 7) for activity in get_activities_by_level(level_id)}
        self.assertGreaterEqual(len(activity_types), 8)
        self.assertIn("written", activity_types)

        student = self.app.test_client()
        for path in ("/", "/register", "/login", "/dashboard", "/profile", "/levels/1", "/cuadernillo/view", "/final-project", "/certificate"):
            self.assertEqual(student.get(path, follow_redirects=True).status_code, 200, path)

        response = student.post(
            "/register",
            data={"username": "Estudiante QA", "email": "estudiante@example.test", "password": "Clave-de-prueba-123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Modo Ruta", response.data)
        self.assertIn(b"Sellado", response.data)
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

        user_before_free_mode = get_user_by_email("estudiante@example.test")
        xp_before_free_mode = user_before_free_mode["xp"]
        disabled = student.post("/api/route-mode", json={"enabled": False})
        self.assertEqual(disabled.status_code, 200)
        self.assertFalse(disabled.get_json()["route_mode"])
        self.assertFalse(get_route_mode(user_before_free_mode["id"]))

        # Free mode bypasses sequence access without creating academic progress.
        self.assertEqual(student.get("/activities/block1-ej-15").status_code, 200)
        self.assertEqual(student.get("/activities/block2-ej-15").status_code, 200)
        free_attempt = student.post(
            "/activities/block1-ej-15/submit",
            json={"completed": False, "correct": 0, "incorrect": 1, "score": 0, "hints_used": 0},
        )
        self.assertEqual(free_attempt.status_code, 200)
        self.assertFalse(free_attempt.get_json()["completed"])
        self.assertEqual(get_user_by_email("estudiante@example.test")["xp"], xp_before_free_mode)
        self.assertFalse(get_activity_progress(2, 15)["completed"])

        # The preference belongs to the student, not the browser session.
        student.get("/logout")
        self.assertEqual(
            student.post("/login", data={"email": "estudiante@example.test", "password": "Clave-de-prueba-123"}, follow_redirects=True).status_code,
            200,
        )
        self.assertEqual(student.get("/activities/block1-ej-15").status_code, 200)
        advanced_completed = student.post(
            "/activities/block1-ej-15/submit",
            json={"completed": True, "correct": 1, "incorrect": 0, "score": 100, "hints_used": 0},
        )
        self.assertEqual(advanced_completed.status_code, 200)
        self.assertGreater(get_user_by_email("estudiante@example.test")["xp"], xp_before_free_mode)

        enabled = student.post("/api/route-mode", json={"enabled": True})
        self.assertEqual(enabled.status_code, 200)
        self.assertTrue(enabled.get_json()["route_mode"])
        self.assertEqual(student.get("/activities/block1-ej-14").status_code, 302)

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

    def test_z_route_mode_update_survives_audit_failure(self):
        student = self.app.test_client()
        response = student.post(
            "/register",
            data={"username": "Ruta Audit", "email": "ruta-audit@example.test", "password": "Clave-de-prueba-123"},
        )
        self.assertEqual(response.status_code, 302)
        with patch("app.interfaces.routes.record_audit_event", side_effect=RuntimeError("audit unavailable")):
            response = student.post("/api/route-mode", json={"enabled": False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["route_mode"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
