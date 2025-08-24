from orchestrator import build_default_orchestrator


def test_routes_to_data_when_context_specifies_data():
    orch = build_default_orchestrator()
    payload = {"context": {"task": "data"}}
    assert orch.route(payload, default="chat") == "data"


def test_routes_to_chat_by_default():
    orch = build_default_orchestrator()
    payload = {"context": {}}
    assert orch.route(payload, default="chat") == "chat"


def test_default_can_be_overridden():
    orch = build_default_orchestrator()
    payload: dict = {}
    assert orch.route(payload, default="data") == "data"
