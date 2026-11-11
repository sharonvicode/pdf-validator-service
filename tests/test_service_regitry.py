import threading
import http.server
import json
import pytest
from app.core.service_registry import register_service, deregister_service, get_container_ip
from app.core.config import Settings

class FakeConsulHandler(http.server.BaseHTTPRequestHandler):
    requests_received = []

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        data = json.loads(body.decode('utf-8')) if body else {}
        FakeConsulHandler.requests_received.append((self.path, data))
        
        if "/v1/agent/service/register" in self.path:
            if "fail_500" in self.path:
                self.send_response(500)
                self.end_headers()
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif "/v1/agent/service/deregister" in self.path:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

@pytest.fixture(scope="module")
def fake_consul():
    server = http.server.HTTPServer(('127.0.0.1', 0), FakeConsulHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()

def test_register_service_success(fake_consul):
    settings = Settings(
        CONSUL_URL=fake_consul,
        CONSUL_SERVICE_NAME="validator",
        PORT=8000
    )
    FakeConsulHandler.requests_received.clear()
    register_service(settings)
    
    assert len(FakeConsulHandler.requests_received) == 1
    path, data = FakeConsulHandler.requests_received[0]
    assert path == "/v1/agent/service/register"
    assert data["Name"] == "validator"
    assert data["Port"] == 8000
    
    expected_ip = get_container_ip()
    assert data["Address"] == expected_ip
    assert data["Check"]["HTTP"] == f"http://{expected_ip}:8000/health"
    assert data["Check"]["Interval"] == "10s"
    assert data["Check"]["Timeout"] == "5s"
    assert data["Check"]["DeregisterCriticalServiceAfter"] == "1m"

def test_deregister_service(fake_consul):
    settings = Settings(
        CONSUL_URL=fake_consul,
        CONSUL_SERVICE_NAME="validator",
        PORT=8000
    )
    FakeConsulHandler.requests_received.clear()
    deregister_service(settings)
    
    assert len(FakeConsulHandler.requests_received) == 1
    path, _ = FakeConsulHandler.requests_received[0]
    assert path == "/v1/agent/service/deregister/validator"

def test_no_consul_url_skips_registration():
    settings = Settings(CONSUL_URL=None)
    register_service(settings)
    deregister_service(settings)

def test_consul_down_fails_fast():
    settings = Settings(CONSUL_URL="http://127.0.0.1:1", CONSUL_SERVICE_NAME="validator", PORT=8000)
    with pytest.raises(Exception):
        register_service(settings)