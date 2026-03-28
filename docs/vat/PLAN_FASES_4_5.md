# Plan: Fases 4 y 5 del DER v4

## Fase 4: Oferta Formativa

### Conceptos
La **Oferta Formativa** es la propuesta educativa de un Centro basada en los planes curriculares.
Vincula: Centro → PlanVersionCurricular con detalles operativos (cupos, período, horarios, etc.)

### 4.1 Modelo `OfertaFormativa`

```python
class OfertaFormativa(SoftDeleteModelMixin, models.Model):
    # Relaciones principales
    centro = FK(Centro, CASCADE, related_name="ofertas_formativas")
    plan_curricular = FK(PlanVersionCurricular, PROTECT, related_name="ofertas")

    # Período
    fecha_inicio = DateField(verbose_name="Fecha de inicio")
    fecha_fin = DateField(verbose_name="Fecha de finalización")

    # Cupos y límites
    cantidad_cupos = PositiveIntegerField(verbose_name="Cantidad de cupos")
    cantidad_minima_inscritos = PositiveIntegerField(default=1)

    # Horario
    horario_desde = TimeField(verbose_name="Horario desde")
    horario_hasta = TimeField(verbose_name="Horario hasta")
    dias_semana = ManyToManyField(Dia, related_name="vat_ofertas_formativas")

    # Presupuesto / Costo
    costo_por_participante = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Estado
    activo = BooleanField(default=True)
    estado = CharField(
        choices=[("planificada", "Planificada"), ("abierta", "Abierta"), ("cerrada", "Cerrada")],
        default="planificada"
    )

    # Auditoría
    creado_por = FK(User, PROTECT)
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_modificacion = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("centro", "plan_curricular", "fecha_inicio", "fecha_fin")
        verbose_name = "Oferta Formativa"
        verbose_name_plural = "Ofertas Formativas"
```

### 4.2 Modelo `InscripcionOferta`

```python
class InscripcionOferta(SoftDeleteModelMixin, models.Model):
    """
    Inscripción de un Ciudadano a una OfertaFormativa
    (Similar a ParticipanteActividad pero para formación)
    """
    oferta = FK(OfertaFormativa, CASCADE, related_name="inscripciones")
    ciudadano = FK(Ciudadano, PROTECT, related_name="vat_inscripciones_oferta")

    estado = CharField(
        choices=[
            ("inscrito", "Inscrito"),
            ("lista_espera", "Lista de Espera"),
            ("completado", "Completado"),
            ("abandonado", "Abandonado"),
            ("rechazado", "Rechazado"),
        ],
        default="inscrito"
    )

    # Auditoría
    fecha_inscripcion = DateTimeField(auto_now_add=True)
    fecha_modificacion = DateTimeField(auto_now=True)
    inscrito_por = FK(User, PROTECT)

    class Meta:
        unique_together = ("oferta", "ciudadano")
        verbose_name = "Inscripción a Oferta Formativa"
        verbose_name_plural = "Inscripciones a Ofertas Formativas"
```

### 4.3 Componentes

- **Admin**: OfertaFormativaAdmin, InscripcionOfertaAdmin
- **Serializers**: OfertaFormativaSerializer, InscripcionOfertaSerializer
- **ViewSets API**: /api/vat/ofertas-formativas/, /api/vat/inscripciones-oferta/
- **Vistas CRUD**: OfertaFormativaListView, CreateView, DetailView, UpdateView, DeleteView
- **Templates**: 4 (list, form, detail, confirm_delete)
- **Formularios**: OfertaFormativaForm, InscripcionOfertaForm
- **Rutas**: /vat/ofertas-formativas/*
- **Servicios**: VAT/services/oferta_service/impl.py (cálculo cupos, lista espera, etc.)

### 4.4 Migraciones

```
VAT/0010_oferta_formativa.py
├── CreateModel(OfertaFormativa)
├── CreateModel(InscripcionOferta)
└── AddIndex, AddConstraint
```

---

## Fase 5: Sistema de Vouchers

### 5.1 Modelos

```python
class Voucher(SoftDeleteModelMixin, models.Model):
    """
    Representa una asignación de crédito de formación a un beneficiario
    """
    beneficiario = FK(Beneficiario, CASCADE, related_name="vat_vouchers")
    programa = FK(Programa, PROTECT, related_name="vat_vouchers")

    cantidad_inicial = PositiveIntegerField()
    cantidad_usada = PositiveIntegerField(default=0)
    cantidad_disponible = PositiveIntegerField()

    fecha_asignacion = DateField()
    fecha_vencimiento = DateField()

    estado = CharField(
        choices=[
            ("activo", "Activo"),
            ("vencido", "Vencido"),
            ("agotado", "Agotado"),
            ("cancelado", "Cancelado"),
        ],
        default="activo"
    )

    class Meta:
        verbose_name = "Voucher"
        verbose_name_plural = "Vouchers"
```

```python
class VoucherRecarga(SoftDeleteModelMixin, models.Model):
    """
    Registro de cada recarga de voucher
    """
    voucher = FK(Voucher, CASCADE, related_name="recargas")
    cantidad = PositiveIntegerField()
    fecha_recarga = DateTimeField(auto_now_add=True)

    motivo = CharField(
        choices=[
            ("automatica", "Recarga Automática"),
            ("manual", "Recarga Manual"),
            ("ajuste", "Ajuste"),
            ("compensacion", "Compensación"),
        ]
    )

    autorizado_por = FK(User, PROTECT)

    class Meta:
        verbose_name = "Recarga de Voucher"
        verbose_name_plural = "Recargas de Voucher"
```

```python
class VoucherUso(SoftDeleteModelMixin, models.Model):
    """
    Registro de uso de voucher (cuando se inscribe a una oferta)
    """
    voucher = FK(Voucher, CASCADE, related_name="usos")
    inscripcion_oferta = FK(InscripcionOferta, CASCADE, related_name="vat_voucher_usos")
    cantidad_usada = PositiveIntegerField()
    fecha_uso = DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Uso de Voucher"
        verbose_name_plural = "Usos de Voucher"
```

```python
class VoucherLog(models.Model):
    """
    Log de auditoría (sin soft delete - es histórico)
    """
    voucher = FK(Voucher, CASCADE, related_name="logs")

    tipo_evento = CharField(
        choices=[
            ("asignacion", "Asignación"),
            ("recarga", "Recarga"),
            ("uso", "Uso"),
            ("vencimiento", "Vencimiento"),
            ("cancelacion", "Cancelación"),
        ]
    )

    cantidad_afectada = IntegerField()
    fecha_evento = DateTimeField(auto_now_add=True)
    usuario = FK(User, PROTECT)
    detalles = JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Log de Voucher"
        verbose_name_plural = "Logs de Voucher"
        ordering = ["-fecha_evento"]
```

### 5.2 Management Command

```
VAT/management/commands/recargar_vouchers.py
├── Command(BaseCommand)
├── add_arguments(--check, --execute, --programa=X, --test)
├── handle()
├── obtener_beneficiarios_activos()
├── validar_elegibilidad()
├── procesar_recarga()
├── registrar_auditoria()
└── enviar_notificacion()
```

### 5.3 Servicio de Vouchers

```
VAT/services/voucher_service/
├── __init__.py
└── impl.py
    ├── VoucherService
    │  ├── crear_voucher()
    │  ├── recargar_voucher()
    │  ├── usar_voucher()
    │  ├── cancelar_voucher()
    │  ├── obtener_disponible()
    │  └── validar_vencimiento()
```

### 5.4 Configuración (settings)

```python
# settings.py
VOUCHER_CONFIG = {
    "ENABLED": True,
    "RECARGA_AUTOMATICA": True,
    "DIA_RECARGA": 1,  # Primer día del mes
    "CANTIDAD_RECARGA": 50,
    "PROGRAMA_DEFECTO": "Programa VAT",
    "DIAS_ANTES_VENCIMIENTO_NOTIFICACION": 7,
}
```

### 5.5 Componentes

- **Admin**: VoucherAdmin, VoucherRecargaAdmin, VoucherUsoAdmin, VoucherLogAdmin
- **Serializers**: VoucherSerializer, VoucherRecargaSerializer, VoucherUsoSerializer
- **ViewSets API**:
  - /api/vat/vouchers/ (read-only mostly)
  - /api/vat/vouchers/{id}/recargar/ (POST)
  - /api/vat/vouchers/{id}/usar/ (POST)
- **Vistas**: VoucherDetailView, VoucherListView (admin only)
- **Templates**: voucher_detail.html, voucher_log.html
- **Management Command**: recargar_vouchers (cron-based)

### 5.6 Migraciones

```
VAT/0011_voucher_models.py
├── CreateModel(Voucher)
├── CreateModel(VoucherRecarga)
├── CreateModel(VoucherUso)
└── CreateModel(VoucherLog)
```

---

## Orden de Implementación Recomendado

### Fase 4 (Oferta Formativa)
1. Crear modelos: OfertaFormativa, InscripcionOferta
2. Migración: 0010
3. Admin registrations
4. Serializers + ViewSets API
5. Vistas CRUD + Templates
6. Formularios
7. Rutas web
8. Servicio: cálculo cupos, lista espera

### Fase 5 (Vouchers)
1. Crear modelos: Voucher, VoucherRecarga, VoucherUso, VoucherLog
2. Migración: 0011
3. Admin registrations
4. Serializers + ViewSets API
5. Management command: recargar_vouchers
6. Servicio: VoucherService
7. Vistas (admin-only, read-only)
8. Configuración en settings
9. Cron job documentation

---

## Estimación

| Fase | Componentes | Tiempo |
|------|-------------|--------|
| 4 | 2 modelos + 10 componentes | ~3-4 horas |
| 5 | 4 modelos + 15 componentes + command | ~4-5 horas |

---

## Archivos a crear/modificar

### Fase 4
```
VAT/models.py (agregar 2 modelos)
VAT/migrations/0010_oferta_formativa.py
VAT/admin.py (2 registrations)
VAT/serializers.py (2 serializers)
VAT/api_views.py (2 ViewSets)
VAT/api_urls.py (2 router.register)
VAT/forms.py (2 forms)
VAT/urls.py (5 rutas)
VAT/views/oferta.py (5 vistas CRUD)
VAT/services/oferta_service/impl.py
VAT/templates/vat/oferta/ (4 templates)
```

### Fase 5
```
VAT/models.py (agregar 4 modelos)
VAT/migrations/0011_voucher_models.py
VAT/admin.py (4 registrations)
VAT/serializers.py (3 serializers)
VAT/api_views.py (3 ViewSets)
VAT/api_urls.py (3 router.register)
VAT/settings.py (VOUCHER_CONFIG)
VAT/management/commands/recargar_vouchers.py
VAT/services/voucher_service/impl.py
VAT/templates/vat/voucher/ (2 templates)
docs/vat/VOUCHER_SETUP.md (configuración cron)
```

---

## Notas Técnicas

### Fase 4
- **Cascada**: OfertaFormativa → InscripcionOferta (CASCADE)
- **SoftDelete**: Ambos modelos
- **Índices**: En (centro, plan_curricular), (oferta, ciudadano)
- **Unique**: Oferta única por (centro, plan, fecha_inicio, fecha_fin)
- **Servicio**: Manejo automático de lista espera

### Fase 5
- **Sin Celery**: Management command + cron
- **VoucherLog**: Sin soft delete (auditoría inmutable)
- **Atomicidad**: Transacciones en recarga y uso
- **Notificaciones**: Email 7 días antes del vencimiento
- **Configuración**: 100% paramétrica (settings.VOUCHER_CONFIG)
