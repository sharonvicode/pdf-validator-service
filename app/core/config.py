"""Configuración del servicio, leída de variables de entorno."""

import os
from dataclasses import dataclass

DEFAULT_MAX_FILE_SIZE_MB = 10
BYTES_PER_MB = 1024 * 1024


@dataclass(frozen=True)
class Settings:
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * BYTES_PER_MB


def get_settings() -> Settings:
    return Settings(
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", DEFAULT_MAX_FILE_SIZE_MB))
    )
