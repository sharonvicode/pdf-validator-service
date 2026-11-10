"""Configuración del servicio, leída de variables de entorno."""

import os
from dataclasses import dataclass

DEFAULT_MAX_FILE_SIZE_MB = 10
BYTES_PER_MB = 1024 * 1024
INVALID_MAX_FILE_SIZE = "MAX_FILE_SIZE_MB debe ser un entero mayor que cero."


@dataclass(frozen=True)
class Settings:
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    CONSUL_URL: str | None = None
    CONSUL_SERVICE_NAME: str = "validator"
    PORT: int = 8000

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

    return Settings(
        max_file_size_mb=max_file_size_mb,
        CONSUL_URL=consul_url,
        CONSUL_SERVICE_NAME=consul_service_name,
        PORT=port,
    )