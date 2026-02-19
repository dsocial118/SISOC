"""Tests for test admision model."""

from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from duplas.models import Dupla


User = get_user_model()


class AdmisionModelSaveTest(TestCase):
    def setUp(self):
        self.abogado = User.objects.create_user(
            username="abogado", first_name="Ana", last_name="Abogada"
        )
        self.tecnico_1 = User.objects.create_user(username="tecnico1")
        self.tecnico_2 = User.objects.create_user(username="tecnico2")

        self.dupla = Dupla.objects.create(
            nombre="Dupla Test", estado="Activo", abogado=self.abogado
        )
        self.dupla.tecnico.add(self.tecnico_1, self.tecnico_2)

        self.comedor = Comedor.objects.create(nombre="Comedor Test", dupla=self.dupla)

    def _create_admision_with_date(self, current_datetime: datetime) -> Admision:
        with mock.patch("django.utils.timezone.now", return_value=current_datetime):
            return Admision.objects.create(comedor=self.comedor)

    def test_updates_estado_mostrar_and_fecha_when_estado_changes(self):
        initial_datetime = timezone.make_aware(
            datetime(2023, 1, 1, 10, 0, 0), timezone.get_current_timezone()
        )
        update_datetime = initial_datetime + timedelta(days=1)
        admision = self._create_admision_with_date(initial_datetime)

        with mock.patch("django.utils.timezone.now", return_value=update_datetime):
            admision.estado_admision = "enviado_a_legales"
            admision.save(update_fields=["estado_admision"])

        admision.refresh_from_db()

        self.assertEqual(admision.estado_mostrar, "Enviado a legales")
        self.assertEqual(admision.fecha_estado_mostrar, update_datetime.date())

    def test_keeps_fecha_estado_mostrar_when_estado_does_not_change(self):
        initial_datetime = timezone.make_aware(
            datetime(2023, 2, 1, 10, 0, 0), timezone.get_current_timezone()
        )
        later_datetime = initial_datetime + timedelta(days=3)
        admision = self._create_admision_with_date(initial_datetime)
        initial_fecha_estado = admision.fecha_estado_mostrar

        with mock.patch("django.utils.timezone.now", return_value=later_datetime):
            admision.observaciones = "Sin cambios en el estado"
            admision.save(update_fields=["observaciones"])

        admision.refresh_from_db()

        self.assertEqual(admision.fecha_estado_mostrar, initial_fecha_estado)
        self.assertEqual(admision.estado_mostrar, "Iniciada")

    def test_update_fields_includes_estado_and_activa(self):
        initial_datetime = timezone.make_aware(
            datetime(2023, 3, 1, 10, 0, 0), timezone.get_current_timezone()
        )
        discard_datetime = initial_datetime + timedelta(days=2)
        admision = self._create_admision_with_date(initial_datetime)

        with mock.patch("django.utils.timezone.now", return_value=discard_datetime):
            admision.estado_admision = "descartado"
            admision.save(update_fields=["estado_admision"])

        admision.refresh_from_db()

        self.assertFalse(admision.activa)
        self.assertEqual(admision.estado_mostrar, "Descartado")
        self.assertEqual(admision.fecha_estado_mostrar, discard_datetime.date())
