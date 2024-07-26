from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [

    # path('hsu_admin/', admin.site.urls),    # TODO crear un honey_pot para controlar intrusiones
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),    
    path('', include('django.contrib.auth.urls')),
    path('', include('Usuarios.urls')),
    path('', include('Configuraciones.urls')),
    path('', include('Inicio.urls')),
    path('', include('Dashboard.urls')),
    path('', include('Legajos.urls')),
    path('', include('SIF_CDIF.urls')),
    path('', include('SIF_CDLE.urls')),
    path('', include('SIF_MILD.urls')),
    path('', include('SIF_PDV.urls')),
    path('', include('SIF_SL.urls')),
    path('', include('SIF_MA.urls')),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]