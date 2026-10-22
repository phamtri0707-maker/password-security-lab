import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from argon2 import PasswordHasher, extract_parameters

from scripts import create_demo_user as demo_module
from src import init_db

# Bí mật tạm để nhập module app; không dùng cho database thật.
with patch.dict(os.environ, {
    "PASSWORD_PEPPER": secrets.token_hex(32),
    "FLASK_SECRET_KEY": secrets.token_hex(32),
}):
    from src import app as app_module


class LoginTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.db_path = Path(temporary_directory.name) / "users.db"
        self.pepper = secrets.token_hex(32)
        self.secret_key = secrets.token_hex(32)
        self.password = secrets.token_urlsafe(16)

        patches = [
            patch.object(init_db, "DB_PATH", self.db_path),
            patch.object(demo_module, "DB_PATH", self.db_path),
            patch.object(app_module, "DB_PATH", self.db_path),
            patch.object(app_module, "PEPPER", self.pepper),
            patch.dict(os.environ, {
                "PASSWORD_PEPPER": self.pepper,
                "FLASK_SECRET_KEY": self.secret_key,
            }),
            patch.dict(app_module.app.config, {
                "TESTING": True,
                "SECRET_KEY": self.secret_key,
            }),
            patch.object(demo_module, "getpass", return_value=self.password),
        ]
        for test_patch in patches:
            test_patch.start()
            self.addCleanup(test_patch.stop)

        with redirect_stdout(StringIO()):
            init_db.init_db()
        self.client = app_module.app.test_client()

    def post_form(self, path="/", data=None):
        # Lấy CSRF token giống trình duyệt mở form trước khi gửi.
        self.client.get("/register" if path == "/register" else "/")
        with self.client.session_transaction() as state:
            token = state["csrf_token"]
        return self.client.post(path, data={**(data or {}), "csrf_token": token})

    def assert_login_failed(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertIn("Username hoặc password không đúng.", response.get_data(as_text=True))
        with self.client.session_transaction() as state:
            self.assertNotIn("user_id", state)

    def create_user(self):
        with redirect_stdout(StringIO()):
            demo_module.create_demo_user()

    def read_hash(self, username="demo"):
        connection = sqlite3.connect(self.db_path)
        try:
            return connection.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()[0]
        finally:
            connection.close()

    def register_user(self, username="student_web", password=None):
        if password is None:
            password = self.password
        return self.post_form("/register", data={
            "username": username,
            "password": password,
            "confirm_password": password,
        })

    def read_users(self):
        connection = sqlite3.connect(self.db_path)
        try:
            return connection.execute(
                "SELECT id, username, password_hash FROM users ORDER BY id"
            ).fetchall()
        finally:
            connection.close()

    def test_demo_stores_argon2id_hash_with_random_salt(self):
        self.create_user()
        first_hash = self.read_hash()
        self.assertTrue(first_hash.startswith("$argon2id$"))
        self.assertNotIn(self.password, first_hash)
        self.assertNotIn(self.pepper, first_hash)
        self.assertTrue(PasswordHasher().verify(first_hash, self.password + self.pepper))
        parameters = extract_parameters(first_hash)
        self.assertEqual(parameters.memory_cost, app_module.PASSWORD_HASHER.memory_cost)
        self.assertEqual(parameters.time_cost, app_module.PASSWORD_HASHER.time_cost)
        self.assertEqual(parameters.parallelism, app_module.PASSWORD_HASHER.parallelism)

        # Chỉ xóa tài khoản trong database tạm để tạo lại cùng đầu vào.
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("DELETE FROM users")
            connection.commit()
        finally:
            connection.close()
        self.create_user()
        self.assertNotEqual(first_hash.split("$")[4], self.read_hash().split("$")[4])

    def test_existing_demo_is_not_overwritten(self):
        self.create_user()
        first_hash = self.read_hash()
        self.create_user()
        self.assertEqual(first_hash, self.read_hash())

    def test_correct_password_succeeds(self):
        self.create_user()
        response = self.post_form(
            data={"username": "demo", "password": self.password}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/home")
        home_response = self.client.get("/home")
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("Đăng nhập thành công", home_response.get_data(as_text=True))
        self.assertIn("demo", home_response.get_data(as_text=True))
        with self.client.session_transaction() as state:
            self.assertEqual(state["username"], "demo")
            self.assertEqual(set(state), {"csrf_token", "user_id", "username"})

    def test_get_shows_login_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('type="submit"', response.get_data(as_text=True))
        self.assertIn('name="csrf_token"', response.get_data(as_text=True))
        self.assertIn("/static/style.css", response.get_data(as_text=True))
        self.assertNotIn("Đăng nhập thành công.", response.get_data(as_text=True))
        self.assertIn("HttpOnly", response.headers["Set-Cookie"])
        self.assertIn("SameSite=Lax", response.headers["Set-Cookie"])

    def test_wrong_password_fails(self):
        self.create_user()
        response = self.post_form(data={"username": "demo", "password": "wrong-password"})
        self.assert_login_failed(response)

    def test_unknown_username_has_same_error(self):
        self.create_user()
        wrong_password = self.post_form(
            data={"username": "demo", "password": "wrong-password"}
        )
        unknown_user = self.post_form(
            data={"username": "unknown-user", "password": self.password}
        )
        self.assert_login_failed(unknown_user)
        self.assertEqual(wrong_password.data, unknown_user.data)

    def test_invalid_inputs_fail(self):
        self.create_user()
        for username, password in [
            ("demo' OR '1'='1", self.password),
            ("demo", ""),
            ("", self.password),
        ]:
            with self.subTest(username=username, password_is_empty=not password):
                response = self.post_form(
                    data={"username": username, "password": password}
                )
                self.assert_login_failed(response)

    def test_different_pepper_fails(self):
        self.create_user()
        with patch.object(app_module, "PEPPER", secrets.token_hex(32)):
            response = self.post_form(
                data={"username": "demo", "password": self.password}
            )
        self.assert_login_failed(response)

    def test_missing_pepper_stops_demo_creation(self):
        with patch.dict(os.environ, {"PASSWORD_PEPPER": ""}):
            with self.assertRaises(SystemExit):
                demo_module.create_demo_user()

    def test_missing_pepper_stops_app_start(self):
        environment = os.environ.copy()
        environment.pop("PASSWORD_PEPPER", None)
        result = subprocess.run(
            [sys.executable, "-B", app_module.__file__],
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Set PASSWORD_PEPPER", result.stderr)

    def test_missing_session_key_stops_app_start(self):
        environment = os.environ.copy()
        environment.pop("FLASK_SECRET_KEY", None)
        result = subprocess.run(
            [sys.executable, "-B", app_module.__file__],
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Set FLASK_SECRET_KEY", result.stderr)

    def test_missing_database_is_not_created(self):
        missing_path = self.db_path.parent / "missing.db"
        with patch.object(demo_module, "DB_PATH", missing_path):
            with self.assertRaises(SystemExit):
                demo_module.create_demo_user()
        self.assertFalse(missing_path.exists())

    def test_home_requires_login(self):
        response = self.client.get("/home")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")

    def test_logout_clears_login_and_blocks_home(self):
        self.create_user()
        self.post_form(data={"username": "demo", "password": self.password})
        response = self.post_form("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        with self.client.session_transaction() as state:
            self.assertNotIn("user_id", state)
            self.assertNotIn("username", state)
        home_response = self.client.get("/home")
        self.assertEqual(home_response.status_code, 302)
        self.assertEqual(home_response.location, "/")
        self.assertEqual(home_response.headers["Cache-Control"], "no-store")

    def test_logout_cannot_use_get(self):
        self.create_user()
        self.post_form(data={"username": "demo", "password": self.password})
        self.assertEqual(self.client.get("/logout").status_code, 405)
        self.assertEqual(self.client.get("/home").status_code, 200)

    def test_forms_require_valid_csrf_token(self):
        self.create_user()
        credentials = {"username": "demo", "password": self.password}
        self.assertEqual(self.client.post("/", data=credentials).status_code, 400)
        self.client.get("/")
        for token in ["wrong-token", "mã-không-đúng"]:
            response = self.client.post("/", data={**credentials, "csrf_token": token})
            self.assertEqual(response.status_code, 400)
        self.post_form(data=credentials)
        self.assertEqual(self.client.post("/logout").status_code, 400)
        self.assertEqual(self.client.get("/home").status_code, 200)

    def test_logged_in_user_goes_to_home(self):
        self.create_user()
        self.post_form(data={"username": "demo", "password": self.password})
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/home")

    def test_get_register_shows_form_and_login_link(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for field in ["username", "password", "confirm_password", "csrf_token"]:
            self.assertIn(f'name="{field}"', html)
        self.assertIn('href="/"', html)
        self.assertIn("/static/style.css", html)
        self.assertIn('href="/register"', self.client.get("/").get_data(as_text=True))

    def test_register_success_redirects_to_login(self):
        response = self.register_user()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        self.assertEqual(len(self.read_users()), 1)
        with self.client.session_transaction() as state:
            self.assertNotIn("user_id", state)

    def test_register_duplicate_username_preserves_original_account(self):
        self.register_user()
        first_hash = self.read_hash("student_web")
        response = self.register_user(password=secrets.token_urlsafe(16))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Username đã được sử dụng.", response.get_data(as_text=True))
        self.assertEqual(len(self.read_users()), 1)
        self.assertEqual(first_hash, self.read_hash("student_web"))

    def test_register_rejects_password_confirmation_mismatch(self):
        response = self.post_form("/register", data={
            "username": "student_web",
            "password": self.password,
            "confirm_password": "does-not-match",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Password xác nhận không khớp.", response.get_data(as_text=True))
        self.assertNotIn(self.password, response.get_data(as_text=True))
        self.assertEqual(self.read_users(), [])

    def test_register_rejects_empty_fields(self):
        valid_data = {
            "username": "student_web",
            "password": self.password,
            "confirm_password": self.password,
        }
        for missing in [
            {"username": ""},
            {"username": "   "},
            {"password": ""},
            {"password": "   ", "confirm_password": "   "},
            {"confirm_password": ""},
        ]:
            with self.subTest(fields=list(missing)):
                response = self.post_form("/register", data={**valid_data, **missing})
                self.assertEqual(response.status_code, 200)
                self.assertIn('role="alert"', response.get_data(as_text=True))
                self.assertEqual(self.read_users(), [])

    def test_register_database_contains_hash_not_plaintext(self):
        self.register_user()
        password_hash = self.read_hash("student_web")
        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertTrue(app_module.PASSWORD_HASHER.verify(
            password_hash, self.password + self.pepper
        ))
        self.assertNotIn(self.password.encode(), self.db_path.read_bytes())
        self.assertNotIn(self.pepper.encode(), self.db_path.read_bytes())
        connection = sqlite3.connect(self.db_path)
        try:
            columns = connection.execute("PRAGMA table_info(users)").fetchall()
        finally:
            connection.close()
        self.assertEqual([column[1] for column in columns],
                         ["id", "username", "password_hash"])

    def test_login_with_registered_account(self):
        # Username được bỏ khoảng trắng hai đầu; password vẫn giữ nguyên.
        password = " " + self.password + " "
        self.register_user(username="  student_web  ", password=password)
        response = self.post_form(data={
            "username": " student_web ", "password": password
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/home")
        home = self.client.get("/home")
        self.assertEqual(home.status_code, 200)
        self.assertIn("student_web", home.get_data(as_text=True))

    def test_register_generates_different_salts_for_same_password(self):
        self.register_user(username="student_one")
        self.register_user(username="student_two")
        first_salt = self.read_hash("student_one").split("$")[4]
        second_salt = self.read_hash("student_two").split("$")[4]
        self.assertNotEqual(first_salt, second_salt)

    def test_register_requires_valid_csrf_token(self):
        data = {
            "username": "student_web",
            "password": self.password,
            "confirm_password": self.password,
        }
        self.assertEqual(self.client.post("/register", data=data).status_code, 400)
        self.client.get("/register")
        response = self.client.post("/register", data={**data, "csrf_token": "wrong"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.read_users(), [])


if __name__ == "__main__":
    unittest.main()
