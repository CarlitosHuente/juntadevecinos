from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from sitio import views as sitio_views

admin.site.site_header = "Administración — Juntas de Vecinos"
admin.site.site_title = "Juntas de Vecinos"
admin.site.index_title = "Panel de gestión"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("verificar/", sitio_views.verificar_form, name="verificar_form"),
    path("verificar/<str:codigo>/", sitio_views.verificar_detalle, name="verificar_detalle"),
    path("", sitio_views.inicio_plataforma, name="inicio_plataforma"),
    path("<slug:junta_slug>/", include("sitio.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
