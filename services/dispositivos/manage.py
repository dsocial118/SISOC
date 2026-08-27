#!/usr/bin/env python
"""Punto de entrada del proceso independiente de Dispositivos."""

import os
import sys
from pathlib import Path


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository_root))
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "services.dispositivos.service_settings"
    )

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
