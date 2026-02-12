import json
import os
import signal
import subprocess
import sys
import time
import unittest
import urllib.request

# Configuration
HOST = "127.0.0.1"
PORT = 5000
BASE_URL = f"http://{HOST}:{PORT}"
PYTHON_EXE = sys.executable
U1 = "t"
P1 = "t"

U2 = "r"
P2 = "r"


class TestChatIntegration(unittest.TestCase):
    server_process = None
    token1 = None
    token2 = None

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
        """Helper to perform POST request with JSON data and return JSON."""
        url = f"{BASE_URL}{endpoint}"

        # 1. Convert dict to JSON string and encode to bytes
        data = json.dumps(data_dict).encode("utf-8")

        # 2. Create request and explicitly set the Content-Type header
        req = urllib.request.Request(
            url, data=data, method="POST", headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req) as response:
                response_body = response.read().decode("utf-8")
                return json.loads(response_body)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                self.fail(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            self.fail(f"Request failed: {e}")

    # Tests are numbered to ensure sequential execution (flow dependence)

    def test_01_create_account(self):
        resp = self._post("/api/user/new", {"username": U1, "password": P1})
        self.assertEqual(resp, {"status": "ok"}, "create account failed")
        resp = self._post("/api/user/new", {"username": U2, "password": P2})
        self.assertEqual(resp, {"status": "ok"}, "create second account failed")

    def test_02_duel_create_account(self):
        resp = self._post("/api/user/new", {"username": U1, "password": P1})
        self.assertNotEqual(resp.get("e"), None, "dual account creation possible")

    def test_03_verify_account(self):
        resp = self._post("/api/user/verify", {"username": U1, "password": P1})
        self.assertEqual(resp, {"status": "ok"}, "verify account failed")
        resp = self._post("/api/user/verify", {"username": U2, "password": P2})
        self.assertEqual(resp, {"status": "ok"}, "verify second account failed")

    def test_04_verify_account_hack(self):
        resp = self._post("/api/user/verify", {"username": U1, "password": "foobar"})
        self.assertNotEqual(
            resp.get("e"),
            None,
            "verify account succeded with wrong password",
        )

    def test_05_generate_token(self):
        resp = self._post(
            "/api/user/generate",
            {"username": U1, "password": P1, "name": "test"},
        )
        token = resp.get("token")
        if not token:
            self.fail(f"Generate token did not return token. Resp: {resp}")
        self.__class__.token1 = token
        resp = self._post(
            "/api/user/generate",
            {"username": U2, "password": P2, "name": "test"},
        )
        token = resp.get("token")
        if not token:
            self.fail(f"Generate secone token did not return token. Resp: {resp}")

        self.__class__.token2 = token

    def test_06_generate_overlap_token(self):
        resp = self._post(
            "/api/user/generate",
            {"username": U1, "password": P1, "name": "test"},
        )
        token = resp.get("token")
        if token:
            self.fail("Token overwritten!")

    def test_07_list_tokens(self):
        resp = self._post("/api/user/tokens", {"username": U1, "password": P1})

        has_test = any(t.get("tokenname") == "test" for t in resp)
        self.assertTrue(has_test, f"Tokens list does not contain 'test'. Resp: {resp}")

    def test_08_verify_token_username(self):
        resp = self._post("/api/token/username", {"token": self.__class__.token1})
        self.assertEqual(
            resp.get("username"), U1, "Token verification returned wrong username"
        )
        resp = self._post("/api/token/username", {"token": self.__class__.token2})
        self.assertEqual(
            resp.get("username"), U2, "Token verification returned wrong username"
        )

    def test_09_create_room(self):
        resp = self._post(
            "/api/rooms/create", {"token": self.__class__.token1, "room": "test"}
        )
        self.assertEqual(resp, {"status": "ok"}, "create room failed")

    def test_10_create_duel_room(self):
        resp = self._post(
            "/api/rooms/create", {"token": self.__class__.token1, "room": "test"}
        )
        self.assertNotEqual(resp.get("e"), None, "room overwritten")

    def test_11_list_rooms(self):
        resp = self._post("/api/rooms/list", {"token": self.__class__.token1})
        self.assertIn("lobby", resp, "Rooms list missing lobby")
        self.assertIn("test", resp, "Rooms list missing test room")

    def test_12_send_message(self):
        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token1,
                "room": "test",
                "message": f"test from {U1}",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send message failed")

    def test_13_get_messages(self):
        resp = self._post("/api/get", {"token": self.__class__.token1, "room": "test"})

        match = False
        for msg in resp:
            if msg.get("author") == U1 and f"test from {U1}" in msg.get("content", ""):
                match = True
                break

        self.assertTrue(match, f"Message from {U1} not found in response. Resp: {resp}")

    def test_14_add_to_room(self):
        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token1,
                "room": "test",
                "message": f"/add {U2}",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send message failed")

        resp = self._post("/api/rooms/list", {"token": self.__class__.token2})
        self.assertIn("test", resp, "Invite failed")

    def test_15_remove_from_room(self):
        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token1,
                "room": "test",
                "message": f"/remove {U2}",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send message failed")

        resp = self._post("/api/rooms/list", {"token": self.__class__.token2})
        self.assertNotIn("test", resp, "Remove command failed")

    def test_16_leave_room(self):
        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token1,
                "room": "test",
                "message": f"/add {U2}",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send /add message failed")

        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token2,
                "room": "test",
                "message": "/leave",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send /leave message failed")

        resp = self._post("/api/rooms/list", {"token": self.__class__.token2})
        self.assertNotIn("test", resp, "Leave failed")

    def test_17_delete_room(self):

        resp = self._post(
            "/api/send",
            {
                "token": self.__class__.token1,
                "room": "test",
                "message": "/delete",
            },
        )
        self.assertEqual(resp, {"status": "ok"}, "send message failed")

        resp = self._post("/api/rooms/list", {"token": self.__class__.token1})
        self.assertNotIn("test", resp, "Leave failed")

    def test_18_test_enter_wrong_room(self):
        resp = self._post("/api/get", {"token": self.__class__.token2, "room": "test"})

        self.assertNotEqual(resp.get("e"), None, "entering unauthorized room possible")

        resp = self._post("/api/get", {"token": self.__class__.token1, "room": "test"})

        self.assertNotEqual(resp.get("e"), None, "entering deleted room possible")

    def test_19_revoke_token(self):
        resp = self._post("/api/token/revoke", {"token": self.__class__.token1})
        self.assertEqual(resp, {"status": "ok"}, "revoke token failed")

    def test_20_change_password(self):
        resp = self._post(
            "/api/user/changepass",
            {"username": U1, "password": P1, "newpass": "r"},
        )
        self.assertEqual(resp, {"status": "ok"}, "change password failed")

    def test_21_check_change_password(self):
        resp = self._post("/api/user/verify", {"username": U1, "password": P1})

        self.assertNotEqual(resp.get("e"), None, "change password failed")


if __name__ == "__main__":
    unittest.main()
