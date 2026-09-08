from comedores.models import Comedor, Nomina
from comedores.services.comedor_service.impl import ComedorService
from comedores.utils import comedor_usa_admision_para_nomina


def get_nomina_queryset_for_comedor(comedor_id):
    """Devuelve la nomina que corresponde al contexto PWA del comedor."""

    comedor = Comedor.objects.select_related("programa").filter(pk=comedor_id).first()
    if not comedor:
        return Nomina.objects.none()

    if comedor_usa_admision_para_nomina(comedor):
        admision = ComedorService.get_admision_vigente_pwa(comedor_id)
        if not admision:
            return Nomina.objects.none()
        return Nomina.objects.filter(admision_id=admision.id)

    return Nomina.objects.filter(comedor_id=comedor_id, admision__isnull=True)
