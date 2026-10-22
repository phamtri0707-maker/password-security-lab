import hmac
import json
import os
import secrets
import sqlite3
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from flask import Flask, abort, redirect, render_template, request, session, url_for


app = Flask(__name__)
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "users.db"
ARGON2_PARAMETERS = json.loads(
    (ROOT_DIR / "src" / "argon2_config.json").read_text(encoding="utf-8")
)
PASSWORD_HASHER = PasswordHasher(**ARGON2_PARAMETERS)
PEPPER = os.environ.get("PASSWORD_PEPPER")
if not PEPPER:
    raise RuntimeError("Set PASSWORD_PEPPER before starting the app.")

app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set FLASK_SECRET_KEY before starting the app.")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Username không tồn tại vẫn đi qua verify để giảm chênh lệch thời gian xử lý.
DUMMY_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe(32) + PEPPER)


@app.before_request
def protect_forms():
    # CSRF token: mã ngẫu nhiên để kiểm tra form được gửi từ phiên hiện tại.
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        submitted = request.form.get("csrf_token", "")
        if not expected or not hmac.compare_digest(expected.encode(), submitted.encode()):
            abort(400)
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)


@app.after_request
def prevent_page_cache(response):
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    message = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            # Dấu ? truyền username như dữ liệu, không ghép vào câu lệnh SQL.
            user = connection.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        finally:
            connection.close()

        stored_hash = user["password_hash"] if user else DUMMY_HASH
        valid_password = False
        try:
            valid_password = PASSWORD_HASHER.verify(stored_hash, password + PEPPER)
        except (VerificationError, InvalidHashError):
            pass

        if user and valid_password:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        message = "Username hoặc password không đúng."

    return render_template("login.html", message=message)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    message = None
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username:
            message = "Vui lòng nhập username."
        elif not password.strip():
            message = "Vui lòng nhập password."
        elif password != confirm_password:
            message = "Password xác nhận không khớp."
        else:
            connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
            try:
                # Dùng cùng pepper và cấu hình với login; salt do thư viện sinh.
                password_hash = PASSWORD_HASHER.hash(password + PEPPER)
                connection.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
                connection.commit()
            except sqlite3.IntegrityError:
                # UNIQUE trong database chặn username trùng, không ghi đè tài khoản.
                message = "Username đã được sử dụng."
            else:
                return redirect(url_for("login"))
            finally:
                connection.close()

    return render_template("register.html", message=message, username=username)


@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", username=session["username"])


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
