from juntas.models import Junta

EXCLUIDOS = {"admin", "static", "media", "verificar"}


class JuntaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.junta = None
        segmento = request.path.strip("/").split("/")[0] if request.path.strip("/") else ""
        if segmento and segmento not in EXCLUIDOS:
            request.junta = Junta.objects.filter(slug=segmento, activa=True).first()
        return self.get_response(request)
