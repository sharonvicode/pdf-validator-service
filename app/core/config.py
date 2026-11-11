"""Configuración del servicio, leída de variables de entorno."""

import json
import os
from dataclasses import dataclass, field

DEFAULT_MAX_FILE_SIZE_MB = 10
BYTES_PER_MB = 1024 * 1024
INVALID_MAX_FILE_SIZE = "MAX_FILE_SIZE_MB debe ser un entero mayor que cero."


@dataclass(frozen=True)
class Settings:
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    CONSUL_URL: str | None = None
    CONSUL_SERVICE_NAME: str = "validator"
    PORT: int = 8000
    CONSUL_SERVICE_TAGS: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_file_size_mb <= 0:
            raise ValueError(INVALID_MAX_FILE_SIZE)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * BYTES_PER_MB


def get_settings() -> Settings:
    raw_max_size = os.getenv("MAX_FILE_SIZE_MB", str(DEFAULT_MAX_FILE_SIZE_MB))
    try:
        max_file_size_mb = int(raw_max_size)
    except ValueError:
        raise ValueError(INVALID_MAX_FILE_SIZE) from None

    consul_url = os.getenv("CONSUL_URL")
    consul_service_name = os.getenv("CONSUL_SERVICE_NAME", "validator")
    
    raw_port = os.getenv("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError:
        port = 8000

    # Parseo de tags como lista JSON para evitar romper comas internas (middlewares de Traefik)
    raw_tags = os.getenv("CONSUL_SERVICE_TAGS", "[]")
    try:
        consul_service_tags = json.loads(raw_tags)
        if not isinstance(consul_service_tags, list):
            consul_service_tags = []
    except json.JSONDecodeError:
        consul_service_tags = []

    return Settings(
        max_file_size_mb=max_file_size_mb,
        CONSUL_URL=consul_url,
        CONSUL_SERVICE_NAME=consul_service_name,
        PORT=port,
        CONSUL_SERVICE_TAGS=consul_service_tags,
    )