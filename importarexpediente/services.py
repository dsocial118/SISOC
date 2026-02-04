from datetime import datetime
from decimal import Decimal
from django.core.exceptions import ValidationError

# Formatos de fecha aceptados
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]

# Mapeo de cabeceras posibles -> campo de modelo
HEADER_MAP = {
	# Expedientes
	"expediente de pago": "expediente_pago",
	# El modelo usa 'expediente_convenio' en lugar de 'resolucion_pago'
	"expediente del convenio": "expediente_convenio",
	# Comedor identificación: SIEMPRE por ID del CSV
	"anexo": "anexo",
	"id": "comedor_id",
	# Organización creadora (variantes con y sin acento)
	"organización": "organizacion_creacion",
	"organizacion": "organizacion_creacion",
	# Total
	"total": "total",
	# Mes y Año
	"mes de pago": "mes_pago",
	"año": "ano",
	# Prestaciones mensuales
	"prestaciones mensuales desayuno": "prestaciones_mensuales_desayuno",
	"prestaciones mensuales almuerzo": "prestaciones_mensuales_almuerzo",
	"prestaciones mensuales merienda": "prestaciones_mensuales_merienda",
	"prestaciones mensuales cena": "prestaciones_mensuales_cena",
	# Montos mensuales (singular)
	"monto mensual desayuno": "monto_mensual_desayuno",
	"monto mensual almuerzo": "monto_mensual_almuerzo",
	"monto mensual merienda": "monto_mensual_merienda",
	"monto mensual cena": "monto_mensual_cena",
	# Montos mensuales (plural variantes del CSV)
	"monto mensuales desayuno": "monto_mensual_desayuno",
	"monto mensuales almuerzo": "monto_mensual_almuerzo",
	"monto mensuales merienda": "monto_mensual_merienda",
	"monto mensuales cena": "monto_mensual_cena",
}

# Etiquetas amigables para usuarios no técnicos
FIELD_LABELS = {
	"expediente_pago": "Expediente de pago",
	"expediente_convenio": "Expediente del convenio",
	"anexo": "Comedor (anexo)",
	"organizacion_creacion": "Organización",
	"total": "Total",
	"mes_pago": "Mes de pago",
	"ano": "Año",
	# Nuevos campos mensuales
	"prestaciones_mensuales_desayuno": "Prestaciones mensuales desayuno",
	"prestaciones_mensuales_almuerzo": "Prestaciones mensuales almuerzo",
	"prestaciones_mensuales_merienda": "Prestaciones mensuales merienda",
	"prestaciones_mensuales_cena": "Prestaciones mensuales cena",
	"monto_mensual_desayuno": "Monto mensual desayuno",
	"monto_mensual_almuerzo": "Monto mensual almuerzo",
	"monto_mensual_merienda": "Monto mensual merienda",
	"monto_mensual_cena": "Monto mensual cena",
}


def parse_date(value):
	if not value:
		return None
	s = str(value).strip()
	for fmt in DATE_FORMATS:
		try:
			return datetime.strptime(s, fmt).date()
		except Exception:
			continue
	try:
		return datetime.fromisoformat(s).date()
	except Exception:
		return None


def parse_decimal(value):
	if value is None or value == "":
		return None
	s = str(value)
	s = s.replace("$", "").replace(" ", "")
	s = s.replace(".", "")
	s = s.replace(",", ".")
	s = s.strip()
	try:
		return Decimal(s)
	except Exception:
		return None


def parse_int(value):
	if value is None or value == "":
		return None
	s = str(value).replace(".", "").replace(",", "").replace(" ", "")
	s = s.strip()
	if not s:
		return None
	try:
		return int(s)
	except Exception:
		return None


def friendly_error_message(exc: Exception) -> str:
	"""Convierte errores técnicos en mensajes claros para usuarios finales."""
	if isinstance(exc, ValidationError):
		if hasattr(exc, "message_dict") and exc.message_dict:
			partes = []
			for campo, mensajes in exc.message_dict.items():
				etiqueta = FIELD_LABELS.get(campo, campo)
				detalle = "; ".join(str(m) for m in mensajes)
				partes.append(f"{etiqueta}: {detalle}")
			return ". ".join(partes)
		if hasattr(exc, "messages"):
			return "; ".join(str(m) for m in exc.messages)
	return (
		"No se pudo procesar la fila. Verifica que las fechas tengan formato DD/MM/AAAA, "
		"los montos sean numéricos y el comedor exista. Detalle: " + str(exc)
	)
