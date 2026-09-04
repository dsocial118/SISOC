"""Consultas estables que PAS expone a otros dominios."""

from dataclasses import dataclass

from pas.models import PasPersona


@dataclass(frozen=True)
class ResumenTitularPAS:
    """DTO público sin referencias a modelos ni querysets de PAS."""

    persona_id: int
    id_persona: int
    estado: str


def obtener_resumen_titular(persona_id: int) -> ResumenTitularPAS | None:
    """Obtiene el estado PAS a partir de un ID primitivo."""

    persona = PasPersona.objects.filter(pk=persona_id).select_related("estado").first()
    if persona is None:
        return None

    return ResumenTitularPAS(
        persona_id=persona.pk,
        id_persona=persona.id_persona,
        estado=persona.estado.nombre,
    )
