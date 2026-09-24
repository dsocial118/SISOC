"""Los workers persistentes descartan conexiones de base de datos rotas."""

import importlib

import pytest
from django.db import OperationalError


@pytest.mark.parametrize(
    ("module_name", "runner_name", "process_name"),
    [
        (
            "ciudadanos.services_importacion_masiva_jobs",
            "run_ciudadanos_import_jobs_worker",
            "process_next_ciudadanos_import_job",
        ),
        (
            "users.services_user_import_jobs",
            "run_user_import_jobs_worker",
            "process_next_user_import_job",
        ),
        (
            "users.services_bulk_credentials_jobs",
            "run_bulk_credentials_jobs_worker",
            "process_next_bulk_credentials_job",
        ),
        (
            "comunicados.services_mailing_jobs",
            "run_mailing_jobs_worker",
            "process_next_mailing_job",
        ),
        (
            "ocr.services_ocr_jobs",
            "run_ocr_jobs_worker",
            "process_next_ocr_job",
        ),
    ],
)
def test_worker_closes_db_connection_after_error_and_before_next_poll(
    mocker, module_name, runner_name, process_name
):
    module = importlib.import_module(module_name)
    events = []
    mocker.patch.object(
        module,
        "close_old_connections",
        side_effect=lambda: events.append("close"),
    )

    def process():
        events.append("process")
        if events.count("process") == 1:
            raise OperationalError("Server has gone away")
        return False

    mocker.patch.object(module, process_name, side_effect=process)
    mocker.patch.object(
        module.time,
        "sleep",
        side_effect=[None, StopIteration],
    )

    with pytest.raises(StopIteration):
        getattr(module, runner_name)()

    assert events[:4] == ["close", "process", "close", "close"]
    assert events.count("process") == 2


def test_encuestas_scheduler_closes_db_connection_after_error(mocker):
    module = importlib.import_module("encuestas.services")
    events = []
    mocker.patch.object(
        module, "close_old_connections", side_effect=lambda: events.append("close")
    )

    def process():
        events.append("process")
        if events.count("process") == 1:
            raise OperationalError("Server has gone away")
        return {"rondas_cerradas": 0, "rondas_abiertas": 0}

    mocker.patch.object(module, "procesar_rondas_pendientes", side_effect=process)
    mocker.patch.object(module.time, "sleep", side_effect=[None, StopIteration])

    with pytest.raises(StopIteration):
        module.run_encuestas_scheduler()

    assert events[:4] == ["close", "process", "close", "close"]
