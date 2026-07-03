"""Saneo de datos de celiaquía.

Aplica retroactivamente las correcciones que el código nuevo solo aplica hacia
adelante. Los expedientes ya procesados en el pasado no se corrigen solos; este
comando los repara:

  1. RENAPER: legajos con estado_validacion_renaper=2 (Rechazado) que siguen
     APROBADO -> se degradan a RECHAZADO y se libera su cupo si lo tenían.
  2. Responsable puro con MATCH: un rol=responsable no es titular y no debe
     quedar marcado MATCH (inflaba el panel "Match" del reporte) -> SIN_CRUCE
     (y se libera cupo si por algún motivo lo tuviera).
  3. Doble rol / beneficiario cuidador SIN_CRUCE: el cruce viejo salteaba a todo
     cuidador, dejando afuera a celíacos que además cuidan a otro celíaco. Se los
     re-evalúa contra el archivo SINTYS del expediente (cruce_excel) por su propio
     documento y, si matchean, se les reserva cupo.
  4. Cupo descuadrado: ProvinciaCupo.usados != cantidad real de titulares con
     cupo vivos (por legajos DENTRO soft-deleted que no liberaron cupo, o por
     contadores huérfanos) -> se recomputa usados.

SEGURO POR DEFECTO: sin --apply solo REPORTA (dry-run, no escribe nada). Con
--apply escribe. Es idempotente: re-ejecutarlo no vuelve a tocar lo ya corregido.

Ejemplos:
  # Ver qué cambiaría en Tucumán (sin escribir):
  python manage.py sanear_celiaquia --provincia 23
  # Aplicar en Tucumán:
  python manage.py sanear_celiaquia --provincia 23 --apply
  # Solo el saneo RENAPER de dos expedientes:
  python manage.py sanear_celiaquia --expedientes 223 237 --renaper --apply
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from celiaquia.models import (
    EstadoCupo,
    Expediente,
    ExpedienteCiudadano,
    ProvinciaCupo,
    ResultadoSintys,
    RevisionTecnico,
)
from celiaquia.services.cupo_service import CupoNoConfigurado, CupoService
from celiaquia.services.familia_service import FamiliaService

ROL_RESPONSABLE = ExpedienteCiudadano.ROLE_RESPONSABLE
ROLES_BENEFICIARIOS = [
    ExpedienteCiudadano.ROLE_BENEFICIARIO,
    ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE,
]


class Command(BaseCommand):
    help = "Sanea datos de celiaquía (RENAPER, responsable-MATCH, doble rol, cupo)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica los cambios. Por defecto es dry-run (no escribe nada).",
        )
        parser.add_argument("--provincia", type=int, help="ID de provincia a sanear.")
        parser.add_argument(
            "--expedientes",
            type=int,
            nargs="+",
            help="IDs de expedientes a sanear.",
        )
        parser.add_argument(
            "--todas",
            action="store_true",
            help="Sanear TODOS los expedientes (requerido si no se pasa alcance).",
        )
        parser.add_argument(
            "--renaper", action="store_true", help="Solo saneo RENAPER."
        )
        parser.add_argument(
            "--responsable-match",
            action="store_true",
            help="Solo limpieza de responsable puro con MATCH.",
        )
        parser.add_argument(
            "--doble-rol",
            action="store_true",
            help="Solo re-evaluar doble rol / beneficiario cuidador SIN_CRUCE.",
        )
        parser.add_argument(
            "--cupo",
            action="store_true",
            help="Solo recomputar ProvinciaCupo.usados (= DENTRO reales vivos).",
        )
        parser.add_argument(
            "--usuario",
            help="username para atribuir los movimientos de cupo (opcional).",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        if not (options["provincia"] or options["expedientes"] or options["todas"]):
            raise CommandError(
                "Definí el alcance: --provincia <id>, --expedientes <ids...> o --todas."
            )

        base = ExpedienteCiudadano.objects.all()
        if options["expedientes"]:
            base = base.filter(expediente_id__in=options["expedientes"])
        elif options["provincia"]:
            base = base.filter(ciudadano__provincia_id=options["provincia"])

        usuario = None
        if options["usuario"]:
            usuario = (
                get_user_model().objects.filter(username=options["usuario"]).first()
            )
            if usuario is None:
                raise CommandError(f"Usuario '{options['usuario']}' no existe.")

        correr_todas = not (
            options["renaper"]
            or options["responsable_match"]
            or options["doble_rol"]
            or options["cupo"]
        )

        modo = "APLICANDO CAMBIOS" if apply else "DRY-RUN (no escribe nada)"
        self.stdout.write(self.style.WARNING(f"== Saneo celiaquía — {modo} =="))
        self.stdout.write(f"Legajos en alcance: {base.count()}")

        resumen = {}
        if correr_todas or options["renaper"]:
            resumen["renaper"] = self._sanear_renaper(base, apply, usuario)
        if correr_todas or options["responsable_match"]:
            resumen["responsable_match"] = self._limpiar_responsable_match(
                base, apply, usuario
            )
        if correr_todas or options["doble_rol"]:
            resumen["doble_rol"] = self._reevaluar_doble_rol(base, apply, usuario)
        if correr_todas or options["cupo"]:
            resumen["cupo"] = self._recomputar_cupo(base, options, apply)

        self.stdout.write(self.style.SUCCESS("\n== Resumen =="))
        for clave, datos in resumen.items():
            self.stdout.write(f"  {clave}: {datos}")
        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    "\nDRY-RUN: no se escribió nada. Reejecutá con --apply para aplicar."
                )
            )

    # ------------------------------------------------------------------ #
    #  1) RENAPER: estado 2 (Rechazado) que sigue APROBADO -> RECHAZADO   #
    # ------------------------------------------------------------------ #
    def _sanear_renaper(self, base, apply, usuario):
        qs = base.filter(
            estado_validacion_renaper=2, revision_tecnico=RevisionTecnico.APROBADO
        ).select_related("ciudadano")
        total = 0
        liberados = 0
        self.stdout.write(self.style.HTTP_INFO("\n[1] RENAPER rechazado -> RECHAZADO"))
        for legajo in qs.iterator():
            total += 1
            self.stdout.write(
                f"  exp={legajo.expediente_id} doc={legajo.ciudadano.documento} "
                f"cupo={legajo.estado_cupo} -> RECHAZADO"
            )
            if not apply:
                continue
            if legajo.estado_cupo == EstadoCupo.DENTRO:
                if self._liberar(legajo, usuario, "Saneo: rechazado en RENAPER"):
                    liberados += 1
            ExpedienteCiudadano.objects.filter(pk=legajo.pk).update(
                revision_tecnico=RevisionTecnico.RECHAZADO
            )
        return {"legajos": total, "cupos_liberados": liberados}

    # ------------------------------------------------------------------ #
    #  2) Responsable puro con MATCH -> SIN_CRUCE                          #
    # ------------------------------------------------------------------ #
    def _limpiar_responsable_match(self, base, apply, usuario):
        qs = base.filter(
            rol=ROL_RESPONSABLE, resultado_sintys=ResultadoSintys.MATCH
        ).select_related("ciudadano")
        total = 0
        liberados = 0
        self.stdout.write(
            self.style.HTTP_INFO("\n[2] Responsable puro con MATCH -> SIN_CRUCE")
        )
        for legajo in qs.iterator():
            total += 1
            self.stdout.write(
                f"  exp={legajo.expediente_id} doc={legajo.ciudadano.documento} "
                f"cupo={legajo.estado_cupo} -> SIN_CRUCE"
            )
            if not apply:
                continue
            if legajo.estado_cupo == EstadoCupo.DENTRO:
                if self._liberar(legajo, usuario, "Saneo: responsable no titular"):
                    liberados += 1
            ExpedienteCiudadano.objects.filter(pk=legajo.pk).update(
                resultado_sintys=ResultadoSintys.SIN_CRUCE,
                cruce_ok=None,
                observacion_cruce=None,
            )
        return {"legajos": total, "cupos_liberados": liberados}

    # ------------------------------------------------------------------ #
    #  3) Doble rol / beneficiario cuidador SIN_CRUCE -> re-evaluar        #
    # ------------------------------------------------------------------ #
    def _reevaluar_doble_rol(self, base, apply, usuario):
        # Import diferido: solo esta corrección necesita leer el Excel SINTYS
        # (CruceService importa pandas).
        from celiaquia.services.cruce_service import (  # pylint: disable=import-outside-toplevel
            CruceService,
        )

        afectados_base = base.filter(
            revision_tecnico=RevisionTecnico.APROBADO,
            resultado_sintys=ResultadoSintys.SIN_CRUCE,
            rol__in=ROLES_BENEFICIARIOS,
        )
        exp_ids = list(
            afectados_base.values_list("expediente_id", flat=True).distinct()
        )
        matched = 0
        no_match = 0
        reservados = 0
        exp_sin_excel = 0
        self.stdout.write(
            self.style.HTTP_INFO(
                "\n[3] Doble rol / beneficiario cuidador SIN_CRUCE -> re-evaluar"
            )
        )
        for exp_id in exp_ids:
            expediente = Expediente.objects.filter(pk=exp_id).first()
            if not expediente or not expediente.cruce_excel:
                exp_sin_excel += 1
                self.stderr.write(
                    self.style.WARNING(
                        f"  exp={exp_id} sin cruce_excel: no se puede re-evaluar."
                    )
                )
                continue
            try:
                ids_archivo = CruceService._leer_identificadores(  # pylint: disable=protected-access
                    expediente.cruce_excel
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                exp_sin_excel += 1
                self.stderr.write(
                    self.style.WARNING(f"  exp={exp_id} cruce_excel ilegible: {exc}")
                )
                continue

            set_cuits = ids_archivo["cuits"]
            set_dnis = ids_archivo["dnis"]

            afectados = list(
                afectados_base.filter(expediente_id=exp_id).select_related("ciudadano")
            )
            # Solo cuidadores principales: son los que el cruce viejo salteaba.
            ciudadanos_ids = [leg.ciudadano_id for leg in afectados]
            cuidadores = FamiliaService.obtener_ids_responsables(ciudadanos_ids)

            for legajo in afectados:
                ciudadano = legajo.ciudadano
                if ciudadano.id not in cuidadores:
                    # No era cuidador: el cruce viejo no lo salteaba, no se toca.
                    continue
                cuit = CruceService.resolver_cuit_ciudadano(ciudadano)
                dni = CruceService.normalize_dni_str(
                    getattr(ciudadano, "documento", "")
                )
                es_match = bool(
                    (cuit and cuit in set_cuits) or (dni and dni in set_dnis)
                )
                self.stdout.write(
                    f"  exp={exp_id} doc={ciudadano.documento} "
                    f"-> {'MATCH' if es_match else 'NO_MATCH'}"
                )
                if es_match:
                    matched += 1
                else:
                    no_match += 1
                if not apply:
                    continue
                if es_match:
                    ExpedienteCiudadano.objects.filter(pk=legajo.pk).update(
                        resultado_sintys=ResultadoSintys.MATCH,
                        cruce_ok=True,
                        observacion_cruce=None,
                    )
                    try:
                        if CupoService.reservar_slot(
                            legajo=legajo,
                            usuario=usuario,
                            motivo="Saneo: doble rol / beneficiario cuidador",
                        ):
                            reservados += 1
                    except CupoNoConfigurado:
                        self.stderr.write(
                            self.style.WARNING(
                                f"  exp={exp_id} sin cupo configurado: no se reservó."
                            )
                        )
                else:
                    ExpedienteCiudadano.objects.filter(pk=legajo.pk).update(
                        resultado_sintys=ResultadoSintys.NO_MATCH,
                        cruce_ok=False,
                        observacion_cruce="No está en archivo de Syntys",
                    )
        return {
            "match": matched,
            "no_match": no_match,
            "cupos_reservados": reservados,
            "expedientes_sin_excel": exp_sin_excel,
        }

    # ------------------------------------------------------------------ #
    #  4) Recompute de ProvinciaCupo.usados                               #
    # ------------------------------------------------------------------ #
    def _recomputar_cupo(self, base, options, apply):
        """Corrige el contador ProvinciaCupo.usados dejándolo igual a la cantidad
        real de titulares con cupo vivos (estado_cupo=DENTRO, no responsables).

        Cubre descuadres por legajos DENTRO soft-deleted que no liberaron cupo y
        contadores huérfanos.
        """
        cupos = ProvinciaCupo.objects.select_related("provincia")
        if options["provincia"]:
            cupos = cupos.filter(provincia_id=options["provincia"])
        elif options["expedientes"]:
            prov_ids = {
                pid
                for pid in base.values_list(
                    "ciudadano__provincia_id", flat=True
                ).distinct()
                if pid
            }
            cupos = cupos.filter(provincia_id__in=prov_ids)

        self.stdout.write(
            self.style.HTTP_INFO("\n[4] Recompute de ProvinciaCupo.usados")
        )
        corregidas = 0
        for pc in cupos:
            real = ExpedienteCiudadano.objects.filter(
                ciudadano__provincia=pc.provincia,
                estado_cupo=EstadoCupo.DENTRO,
                rol__in=ROLES_BENEFICIARIOS,
            ).count()
            if pc.usados != real:
                corregidas += 1
                self.stdout.write(
                    f"  {pc.provincia}: usados {pc.usados} -> {real} "
                    f"(dif {pc.usados - real})"
                )
                if apply:
                    ProvinciaCupo.objects.filter(pk=pc.pk).update(usados=real)
        return {"provincias_corregidas": corregidas}

    # ------------------------------------------------------------------ #
    def _liberar(self, legajo, usuario, motivo):
        try:
            return CupoService.liberar_slot(
                legajo=legajo, usuario=usuario, motivo=motivo
            )
        except CupoNoConfigurado:
            self.stderr.write(
                self.style.WARNING(
                    f"  exp={legajo.expediente_id} sin cupo configurado: no se liberó."
                )
            )
            return False
