import json
import logging
import urllib.request
import urllib.error
from app.core.config import Settings

logger = logging.getLogger(__name__)

def register_service(settings: Settings) -> None:
    if not getattr(settings, "CONSUL_URL", None):
        return
    
    payload = {
        "Name": getattr(settings, "CONSUL_SERVICE_NAME", "validator"),
        "Port": getattr(settings, "PORT", 8000),
        "Check": {
            "HTTP": f"http://host.docker.internal:{getattr(settings, 'PORT', 8000)}/health",
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