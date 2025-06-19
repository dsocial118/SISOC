from django.contrib import admin

from rendicioncuentasfinal.models import (
    DocumentoRendicionFinal,
    EstadoDocumentoRendicionFinal,
    RendicionCuentasFinal,
    TipoDocumentoRendicionFinal,
)


admin.site.register(RendicionCuentasFinal)
admin.site.register(EstadoDocumentoRendicionFinal)
admin.site.register(TipoDocumentoRendicionFinal)
admin.site.register(DocumentoRendicionFinal)
