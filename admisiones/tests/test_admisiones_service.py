"""Tests for test admisiones service."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from admisiones.models.admisiones import Admision
from admisiones.services.admisiones_service import AdmisionService
from comedores.models import Comedor
from duplas.models import Dupla


User = get_user_model()


class AdmisionServiceTest(TestCase):
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
        self.admision = Admision.objects.create(comedor=self.comedor)

    def test_abogado_queryset_has_no_duplicates(self):
        queryset = AdmisionService.get_admisiones_tecnicos_queryset(self.abogado)

        admisiones_ids = list(queryset.values_list("id", flat=True))
        self.assertEqual(admisiones_ids, [self.admision.id])

    def test_tecnico_queryset_has_no_duplicates(self):
        queryset = AdmisionService.get_admisiones_tecnicos_queryset(self.tecnico_1)

        admisiones_ids = list(queryset.values_list("id", flat=True))
        self.assertEqual(admisiones_ids, [self.admision.id])
