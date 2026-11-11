import json
import logging
import socket
import urllib.request
import urllib.error
from app.core.config import Settings

logger = logging.getLogger(__name__)


def get_container_ip() -> str:
    """Obtiene la IP local del contenedor para el healthcheck y la dirección en Consul."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


def register_service(settings: Settings) -> None:
    if not getattr(settings, "CONSUL_URL", None):
        return
    
    service_ip = get_container_ip()
    service_name = getattr(settings, "CONSUL_SERVICE_NAME", "validator")
    port = getattr(settings, "PORT", 8000)
    tags = getattr(settings, "CONSUL_SERVICE_TAGS", [])

    payload = {
        "Name": service_name,
        "Address": service_ip,
        "Port": port,
        "Tags": tags,
        "Check": {
            "HTTP": f"http://{service_ip}:{port}/health",
            "Interval": "10s",
            "Timeout": "5s",
            "DeregisterCriticalServiceAfter": "1m"
        }
    }
    
    url = f"{settings.CONSUL_URL.rstrip('/')}/v1/agent/service/register"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status not in (200, 204):
                raise RuntimeError(f"Failed to register service in Consul: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error connecting to Consul for registration: {e}")
        raise


def deregister_service(settings: Settings) -> None:
    if not getattr(settings, "CONSUL_URL", None):
        return
    
    service_name = getattr(settings, "CONSUL_SERVICE_NAME", "validator")
    url = f"{settings.CONSUL_URL.rstrip('/')}/v1/agent/service/deregister/{service_name}"
    req = urllib.request.Request(url, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status not in (200, 204):
                logger.warning(f"Failed to deregister service from Consul: HTTP {response.status}")
    except Exception as e:
        logger.warning(f"Error connecting to Consul for deregistration: {e}")