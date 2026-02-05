import unittest
import urllib.request
import urllib.parse
import json
import subprocess
import sys
import time
import os
import signal

# Configuration
HOST = "127.0.0.1"
PORT = 5000
BASE_URL = f"http://{HOST}:{PORT}"
PYTHON_EXE = sys.executable
USERNAME = "t"
PASSWORD = "t"


class TestChatIntegration(unittest.TestCase):
    server_process = None
    token = None

    @classmethod
    def setUpClass(cls):
        """
        Initializes DB, starts server, and waits for availability.
        """

        print(f"Setting up test environment using {PYTHON_EXE}...")

        env = os.environ.copy()
        env["FLASK_APP"] = "app.py"
        env["FLASK_RUN_HOST"] = HOST
        env["FLASK_RUN_PORT"] = str(PORT)

        print("Initializing database...")
        subprocess.run([PYTHON_EXE, "-m", "flask", "init"], env=env, check=True)

        print("Starting Flask server...")

        cls.server_process = subprocess.Popen(
            [PYTHON_EXE, "-m", "flask", "run"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        timeout = 30
        start_time = time.time()
        print("Waiting for server to be responsive...")

        while time.time() - start_time < timeout:
            try:
                with urllib.request.urlopen(f"{BASE_URL}/") as response:
                    if response.status == 200:
                        print("Server is up.")
                        return
            except Exception:
                time.sleep(1)

        # If we reach here, server didn't start
        cls.tearDownClass()
        raise RuntimeError(f"Server failed to start within {timeout} seconds")

    @classmethod
    def tearDownClass(cls):
        """
        Kills flask server.
        """
        print("\nTeardown: Stopping server...")
        if cls.server_process:
            try:
                os.killpg(os.getpgid(cls.server_process.pid), signal.SIGTERM)
                cls.server_process.wait(timeout=2)
            except Exception:
                try:
                    os.killpg(os.getpgid(cls.server_process.pid), signal.SIGKILL)
                except Exception:
                    pass

    def _post(self, endpoint, data_dict):
        """Helper to perform POST request with form data and return JSON."""
        url = f"{BASE_URL}{endpoint}"
        # Convert dict to application/x-www-form-urlencoded
        data = urllib.parse.urlencode(data_dict).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode("utf-8")
                return json.loads(response_body)
        except urllib.error.HTTPError as e:
            # If the server returns a 4xx/5xx with JSON error message, read it
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                self.fail(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            self.fail(f"Request failed: {e}")

    # Tests are numbered to ensure sequential execution (flow dependence)

    def test_01_create_account(self):
        resp = self._post("/api/user/new", {"username": USERNAME, "password": PASSWORD})
        self.assertEqual(resp, {"status": "ok"}, "create account failed")

    def test_02_duel_create_account(self):
        resp = self._post("/api/user/new", {"username": USERNAME, "password": PASSWORD})
        self.assertNotEqual(resp.get("e"), None, "dual account creation possible")

    def test_03_verify_account(self):
        resp = self._post(
            "/api/user/verify", {"username": USERNAME, "password": PASSWORD}
        )
        self.assertEqual(resp, {"status": "ok"}, "verify account failed")

    def test_04_verify_account_hack(self):
        resp = self._post(
            "/api/user/verify", {"username": USERNAME, "password": "foobar"}
        )
        self.assertNotEqual(
            resp.get("e"),
            {"status": "ok"},
            "verify account succeded with wrong password",
        )

    def test_05_generate_token(self):
        resp = self._post(
            "/api/user/generate",
            {"username": USERNAME, "password": PASSWORD, "name": "test"},
        )
        token = resp.get("token")
        if not token:
            self.fail(f"Generate token did not return token. Resp: {resp}")

        # Store token in class variable for subsequent tests
        self.__class__.token = token
        print(f"Token generated: {token}")

    def test_06_generate_overlap_token(self):
        resp = self._post(
            "/api/user/generate",
            {"username": USERNAME, "password": PASSWORD, "name": "test"},
        )
        token = resp.get("token")
        if token:
            self.fail(f"Token overwritten!")

    def test_07_list_tokens(self):
        resp = self._post(
            "/api/user/tokens", {"username": USERNAME, "password": PASSWORD}
        )

        has_test = any(t.get("tokenname") == "test" for t in resp)
        self.assertTrue(has_test, f"Tokens list does not contain 'test'. Resp: {resp}")

    def test_08_verify_token_username(self):
        resp = self._post("/api/token/username", {"token": self.__class__.token})
        self.assertEqual(
            resp.get("username"), USERNAME, "Token verification returned wrong username"
        )

    def test_09_create_room(self):
        resp = self._post(
            "/api/rooms/create", {"token": self.__class__.token, "room": "test"}
        )
        self.assertEqual(resp, {"status": "ok"}, "create room failed")

    def test_10_create_duel_room(self):
        resp = self._post(
            "/api/rooms/create", {"token": self.__class__.token, "room": "test"}
        )
        self.assertNotEqual(resp.get("e"), None, "room overwritten")

    def test_11_list_rooms(self):
        resp = self._post("/api/rooms/list", {"token": self.__class__.token})
        self.assertIn("lobby", resp, "Rooms list missing lobby")
        self.assertIn("test", resp, "Rooms list missing test room")

    def test_12_send_message(self):
        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token,
                "room": "test",
                "message": f"test from {USERNAME}",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send message failed")

    def test_13_get_messages(self):
        resp = self._post("/api/get", {"token": self.__class__.token, "room": "test"})

        match = False
        for msg in resp:
            if msg.get("author") == USERNAME and f"test from {USERNAME}" in msg.get(
                "content", ""
            ):
                match = True
                break

        self.assertTrue(
            match, f"Message from {USERNAME} not found in response. Resp: {resp}"
        )

    def test_14_revoke_token(self):
        resp = self._post("/api/token/revoke", {"token": self.__class__.token})
        self.assertEqual(resp, {"status": "ok"}, "revoke token failed")

    def test_15_change_password(self):
        resp = self._post(
            "/api/user/changepass",
            {"username": USERNAME, "password": PASSWORD, "newpass": "r"},
        )
        self.assertEqual(resp, {"status": "ok"}, "change password failed")

    def test_16_check_change_password(self):
        resp = self._post(
            "/api/user/verify", {"username": USERNAME, "password": PASSWORD}
        )

        self.assertNotEqual(resp.get("e"), None, "change password failed")


if __name__ == "__main__":
    unittest.main()
