"""Reinicio y checkpoints de la importación de usuarios."""

from datetime import timedelta
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import UserImportJob, UserImportJobRow
from users.services_user_import_jobs import (
    LostImportLease,
    _start_job_row_attempt,
    claim_next_user_import_job,
    mark_stale_user_import_jobs_as_failed,
    process_user_import_job,
)


User = get_user_model()


@pytest.mark.django_db
def test_stale_user_import_requeues_and_old_worker_cannot_write():
    owner = User.objects.create_user(username="user_import_lease_owner")
    job = UserImportJob.objects.create(
        requested_by=owner,
        original_filename="usuarios.xlsx",
        archivo="users/import_jobs/test/usuarios.xlsx",
        status=UserImportJob.Status.PROCESSING,
        lease_token=uuid.uuid4(),
        last_activity_at=timezone.now() - timedelta(seconds=901),
    )

    assert mark_stale_user_import_jobs_as_failed() == 1
    with pytest.raises(LostImportLease):
        _start_job_row_attempt(
            job=job,
            row_index=0,
            row_data={"fila": 2, "correo": "persona@example.com"},
        )

    job.refresh_from_db()
    assert job.status == UserImportJob.Status.PENDING
    assert job.resume_count == 1
    assert job.next_row_index == 0


@pytest.mark.django_db
def test_user_import_yields_to_other_job_and_resumes(mocker):
    owner = User.objects.create_user(username="user_import_fair_queue")
    large = UserImportJob.objects.create(
        requested_by=owner,
        original_filename="grande.xlsx",
        archivo="users/import_jobs/test/grande.xlsx",
        send_credentials=False,
    )
    small = UserImportJob.objects.create(
        requested_by=owner,
        original_filename="chico.xlsx",
        archivo="users/import_jobs/test/chico.xlsx",
        send_credentials=False,
    )
    mocker.patch(
        "users.services_user_import_jobs.get_user_import_job_slice_seconds",
        return_value=0,
    )
    mocker.patch(
        "users.services_user_import_jobs._load_job_rows",
        side_effect=lambda job: [
            {"fila": index + 2, "correo": f"persona{index}@example.com"}
            for index in range(2 if job.pk == large.pk else 1)
        ],
    )
    mocker.patch(
        "users.services_user_import_jobs.process_single_user_import_row",
        return_value={"status": UserImportJobRow.Status.SKIPPED, "mensaje": "Omitido"},
    )

    process_user_import_job(large)
    large.refresh_from_db()
    assert large.status == UserImportJob.Status.PENDING
    assert large.next_row_index == 1

    claimed_small = claim_next_user_import_job()
    assert claimed_small.pk == small.pk
    process_user_import_job(claimed_small)
    resumed = claim_next_user_import_job()
    assert resumed.pk == large.pk
    process_user_import_job(resumed)

    large.refresh_from_db()
    assert large.status == UserImportJob.Status.COMPLETED
    assert large.processed_rows == 2
    assert list(large.rows.order_by("fila").values_list("attempts", flat=True)) == [
        1,
        1,
    ]


@pytest.mark.django_db
def test_user_creation_rolls_back_if_row_checkpoint_fails(mocker):
    owner = User.objects.create_user(username="user_import_atomic_owner")
    job = UserImportJob.objects.create(
        requested_by=owner,
        original_filename="usuarios.xlsx",
        archivo="users/import_jobs/test/usuarios.xlsx",
        send_credentials=False,
    )
    mocker.patch(
        "users.services_user_import_jobs._load_job_rows",
        return_value=[{"fila": 2, "correo": "nueva@example.com"}],
    )

    def create_user(*, row_data, job):
        created = User.objects.create_user(
            username="user_import_atomic_created", email=row_data["correo"]
        )
        return {
            "status": UserImportJobRow.Status.CREATED,
            "mensaje": "Creado",
            "email": row_data["correo"],
            "created_user_id": created.pk,
        }

    mocker.patch(
        "users.services_user_import_jobs.process_single_user_import_row",
        side_effect=create_user,
    )
    mocker.patch(
        "users.services_user_import_jobs._record_row_created",
        side_effect=RuntimeError("checkpoint falló"),
    )

    with pytest.raises(RuntimeError, match="checkpoint falló"):
        process_user_import_job(job)

    assert not User.objects.filter(username="user_import_atomic_created").exists()
    job.refresh_from_db()
    assert job.next_row_index == 0
