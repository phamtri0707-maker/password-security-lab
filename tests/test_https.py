import os
import runpy
import secrets
import shutil
import socket
import sqlite3
import ssl
import subprocess
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, HTTPSHandler, ProxyHandler, Request, build_opener

from werkzeug.serving import make_server

from src import init_db

with patch.dict(os.environ, {
    "PASSWORD_PEPPER": secrets.token_hex(32),
    "FLASK_SECRET_KEY": secrets.token_hex(32),
}):
    from src import app as app_module


class HttpsStartupTests(unittest.TestCase):
    def startup_environment(self):
        return {
            "PASSWORD_PEPPER": secrets.token_hex(32),
            "FLASK_SECRET_KEY": secrets.token_hex(32),
            "TLS_CERT_FILE": "",
            "TLS_KEY_FILE": "",
        }

    def test_startup_requires_both_tls_paths(self):
        for paths in [{}, {"TLS_CERT_FILE": "cert.pem"}, {"TLS_KEY_FILE": "key.pem"}]:
            with self.subTest(configured_paths=list(paths)):
                environment = {**self.startup_environment(), **paths}
                with patch.dict(os.environ, environment), patch("flask.Flask.run") as run:
                    with self.assertRaisesRegex(RuntimeError, "TLS_CERT_FILE and TLS_KEY_FILE"):
                        runpy.run_path(app_module.__file__, run_name="__main__")
                    run.assert_not_called()

    def test_startup_passes_certificate_and_key_to_flask(self):
        with tempfile.TemporaryDirectory() as directory:
            cert = str(Path(directory) / "cert.pem")
            key = str(Path(directory) / "key.pem")
            environment = {
                **self.startup_environment(),
                "TLS_CERT_FILE": cert,
                "TLS_KEY_FILE": key,
            }
            with (
                patch.dict(os.environ, environment),
                patch("ssl.SSLContext.load_cert_chain") as load_cert_chain,
                patch("flask.Flask.run") as run,
            ):
                runpy.run_path(app_module.__file__, run_name="__main__")
            load_cert_chain.assert_called_once_with(cert, key)
            context = run.call_args.kwargs["ssl_context"]
            handler = run.call_args.kwargs["request_handler"]
            self.assertIsInstance(context, ssl.SSLContext)
            self.assertEqual(context.protocol, ssl.PROTOCOL_TLS_SERVER)
            self.assertEqual(handler.timeout, 10)
            run.assert_called_once_with(
                host="127.0.0.1", port=5000, ssl_context=context,
                request_handler=handler, threaded=True,
            )


class FormTokenParser(HTMLParser):
    token = None

    def handle_starttag(self, tag, attributes):
        fields = dict(attributes)
        if tag == "input" and fields.get("name") == "csrf_token":
            self.token = fields.get("value")


class QuietRequestHandler(app_module.LocalHTTPSRequestHandler):
    def log(self, log_type, message, *arguments):
        pass


class LiveHttpsTests(unittest.TestCase):
    def test_real_tls_register_login_logout(self):
        openssl = shutil.which("openssl")
        if not openssl:
            git_openssl = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/usr/bin/openssl.exe"
            if git_openssl.is_file():
                openssl = str(git_openssl)
        if not openssl:
            self.skipTest("OpenSSL is needed to generate a temporary lab certificate.")

        # Certificate, key, database và secrets đều tạm; không dùng users.db thật.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        temporary_path = Path(directory.name)
        cert = temporary_path / "cert.pem"
        key = temporary_path / "key.pem"
        subprocess.run([
            openssl, "req", "-x509", "-newkey", "rsa:2048", "-sha256", "-nodes",
            "-days", "1", "-keyout", str(key), "-out", str(cert),
            "-subj", "/CN=127.0.0.1",
            "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost",
        ], check=True, capture_output=True, timeout=30)

        db_path = temporary_path / "users.db"
        pepper = secrets.token_hex(32)
        for test_patch in [
            patch.object(init_db, "DB_PATH", db_path),
            patch.object(app_module, "DB_PATH", db_path),
            patch.object(app_module, "PEPPER", pepper),
            patch.dict(app_module.app.config, {
                "TESTING": True, "SECRET_KEY": secrets.token_hex(32),
            }),
        ]:
            test_patch.start()
            self.addCleanup(test_patch.stop)
        with redirect_stdout(StringIO()):
            init_db.init_db()

        connection_started = threading.Event()

        class ConnectionTrackingHandler(QuietRequestHandler):
            def setup(self):
                super().setup()
                connection_started.set()

        tls_context = app_module.LocalHTTPSContext(ssl.PROTOCOL_TLS_SERVER)
        tls_context.load_cert_chain(str(cert), str(key))
        server = make_server(
            "127.0.0.1", 0, app_module.app,
            ssl_context=tls_context, request_handler=ConnectionTrackingHandler,
            threaded=True,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def stop_server():
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.addCleanup(stop_server)
        origin = f"https://127.0.0.1:{server.server_port}"
        trusted_context = ssl.create_default_context(cafile=str(cert))

        # Mặc định self-signed không được tin cậy; tin cert vẫn phải đúng hostname.
        for context, hostname in [
            (ssl.create_default_context(), "127.0.0.1"),
            (trusted_context, "wrong.localhost"),
        ]:
            with self.subTest(hostname=hostname):
                with socket.create_connection(("127.0.0.1", server.server_port), timeout=5) as connection:
                    with self.assertRaises(ssl.SSLCertVerificationError):
                        context.wrap_socket(connection, server_hostname=hostname)

        cookies = CookieJar()
        browser = build_opener(
            ProxyHandler({}), HTTPSHandler(context=trusted_context), HTTPCookieProcessor(cookies)
        )

        def visit(path, data=None, timeout=10):
            body = None if data is None else urlencode(data).encode("utf-8")
            with browser.open(origin + path, data=body, timeout=timeout) as response:
                return response.url, response.read().decode("utf-8"), response.headers

        def token(html):
            parser = FormTokenParser()
            parser.feed(html)
            self.assertIsNotNone(parser.token)
            return parser.token

        # An idle browser preconnection must not block other TLS handshakes.
        connection_started.clear()
        with socket.create_connection(("127.0.0.1", server.server_port), timeout=2):
            self.assertTrue(connection_started.wait(timeout=2))
            _, form, headers = visit("/register", timeout=2)
        for attribute in ["Secure", "HttpOnly", "SameSite=Lax"]:
            self.assertIn(attribute, headers["Set-Cookie"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        insecure_request = Request(origin.replace("https://", "http://") + "/")
        cookies.add_cookie_header(insecure_request)
        self.assertFalse(insecure_request.has_header("Cookie"))

        password = secrets.token_urlsafe(24)
        url, login_form, _ = visit("/register", {
            "username": "tls_student", "password": password,
            "confirm_password": password, "csrf_token": token(form),
        })
        self.assertEqual(urlsplit(url).path, "/")
        self.assertEqual(urlsplit(visit("/home")[0]).path, "/")
        url, home, _ = visit("/", {
            "username": "tls_student", "password": password,
            "csrf_token": token(login_form),
        })
        self.assertEqual(urlsplit(url).path, "/home")
        self.assertIn("Đăng nhập thành công", home)
        self.assertIn("tls_student", home)
        self.assertNotIn(pepper, home)
        self.assertNotIn(password, home)

        url, _, _ = visit("/logout", {"csrf_token": token(home)})
        self.assertEqual(urlsplit(url).path, "/")
        self.assertEqual(urlsplit(visit("/home")[0]).path, "/")
        connection = sqlite3.connect(db_path)
        try:
            password_hash = connection.execute("SELECT password_hash FROM users").fetchone()[0]
        finally:
            connection.close()
        self.assertTrue(app_module.PASSWORD_HASHER.verify(password_hash, password + pepper))


if __name__ == "__main__":
    unittest.main()
