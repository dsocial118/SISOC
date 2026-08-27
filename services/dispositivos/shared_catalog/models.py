"""Proyección read-only de las tablas territoriales compartidas del monolito."""

from django.db import models


class Provincia(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        app_label = "core"
        db_table = "core_provincia"
        managed = False
        ordering = ["id"]


class Municipio(models.Model):
    nombre = models.CharField(max_length=255)
    provincia = models.ForeignKey(
        Provincia,
        db_column="provincia_id",
        db_constraint=False,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    class Meta:
        app_label = "core"
        db_table = "core_municipio"
        managed = False
        ordering = ["id"]
