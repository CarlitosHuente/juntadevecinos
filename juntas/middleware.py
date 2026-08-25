from pathlib import Path

from django.conf import settings
from django.shortcuts import render

from juntas.models import Junta

EXCLUIDOS = {"admin", "static", "media", "verificar"}
RUTAS_LIBRES = ("/admin/", "/static/", "/media/")


def sitio_en_construccion() -> bool:
    if getattr(settings, "SITIO_EN_CONSTRUCCION", False):
        return True
    return (Path(settings.BASE_DIR) / "tmp" / "en_construccion").exists()


class JuntaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.junta = None
        segmento = request.path.strip("/").split("/")[0] if request.path.strip("/") else ""
        if segmento and segmento not in EXCLUIDOS:
            request.junta = Junta.objects.filter(slug=segmento, activa=True).first()
        return self.get_response(request)


class ConstruccionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not sitio_en_construccion():
            return self.get_response(request)
        if request.path.startswith(RUTAS_LIBRES):
            return self.get_response(request)
        if getattr(request.user, "is_staff", False):
            return self.get_response(request)
        junta = getattr(request, "junta", None) or Junta.objects.filter(activa=True).first()
        return render(request, "sitio/en_construccion.html", {"junta": junta})
