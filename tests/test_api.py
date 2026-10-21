import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app, CONFIG  # noqa: E402

client = TestClient(app)
HEAD = {"X-Admin-Token": CONFIG.get("admin_token", "")}


def ask(msg, sid=None):
    r = client.post("/chat", json={"message": msg, "session_id": sid})
    assert r.status_code == 200, r.text
    return r.json()


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_core_intents():
    cases = {
        "hello": "greeting",
        "how much is a 75 inch interactive panel": "pricing",
        "do you have an office in Nanyuki": "location",
        "can i get a free demo": "demo_request",
        "how long is the warranty": "warranty",
        "my cctv stopped working": "maintenance_support",
    }
    for msg, expected in cases.items():
        got = ask(msg)
        assert got["intent"] == expected, (msg, got)


def test_fallback_has_phone():
    got = ask("qwerty zxcvb asdfgh")
    assert got["source"] == "fallback"
    assert "+254 763 502654" in got["response"]
    assert "+971 56 1353 249" in got["response"]
    assert "info@vaultelectronics.co.ke" in got["response"]
    assert "info@vaultelectronics.ae" in got["response"]


def test_contact_answer_has_updated_details():
    got = ask("what are your contact details")
    assert got["intent"] == "contact"
    assert "+254 763 502654" in got["response"]
    assert "+971 56 1353 249" in got["response"]
    assert "info@vaultelectronics.co.ke" in got["response"]
    assert "info@vaultelectronics.ae" in got["response"]


def test_followup_yes_accepts_offer():
    first = ask("what is the price of a panel")
    second = ask("yes", first["session_id"])
    assert second["intent"] == "quote_request"


def test_feedback_and_stats():
    got = ask("hi")
    assert client.post("/feedback", json={"message_id": got["message_id"], "rating": 1}).status_code == 200
    assert client.post("/feedback", json={"message_id": 999999, "rating": 1}).status_code == 404
    assert client.post("/feedback", json={"message_id": got["message_id"], "rating": 5}).status_code == 422
    assert client.get("/stats", headers=HEAD).status_code == 200
    assert client.get("/stats", headers={"X-Admin-Token": "wrong"}).status_code == 401


def test_validation():
    assert client.post("/chat", json={"message": ""}).status_code == 422
    assert client.post("/chat", json={"message": "x" * 501}).status_code == 422
