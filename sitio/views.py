from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from contenido.models import Evento, Noticia
from juntas.models import Junta
from sitio.carrusel import slides_home
from sitio.rate_limit import exceso_intentos, ip_cliente
from transparencia.models import InformeActividad, RendicionGasto
from vecinos.models import Certificado
from vecinos.services import emitir_certificado_web, pdf_de_certificado


def _junta(request, junta_slug: str) -> Junta:
    junta = getattr(request, "junta", None)
    if not junta or junta.slug != junta_slug:
        raise Http404("Junta no encontrada")
    return junta


def inicio_plataforma(request):
    junta = Junta.objects.filter(slug="huente", activa=True).first()
    if junta:
        return redirect("home", junta_slug=junta.slug)
    primera = Junta.objects.filter(activa=True).first()
    if primera:
        return redirect("home", junta_slug=primera.slug)
    return render(request, "sitio/sin_juntas.html")


def home(request, junta_slug):
    junta = _junta(request, junta_slug)
    noticias = Noticia.objects.filter(junta=junta, publicada=True)[:3]
    eventos = Evento.objects.filter(junta=junta, publicado=True, fecha_inicio__gte=timezone.now())[:3]
    return render(
        request,
        "sitio/home.html",
        {
            "slides": slides_home(junta),
            "noticias": noticias,
            "eventos": eventos,
        },
    )


def quienes_somos(request, junta_slug):
    junta = _junta(request, junta_slug)
    return render(
        request,
        "sitio/quienes_somos.html",
        {"cargos": junta.cargos.all()},
    )


def noticias_lista(request, junta_slug):
    junta = _junta(request, junta_slug)
    noticias = Noticia.objects.filter(junta=junta, publicada=True)
    return render(request, "sitio/noticias_lista.html", {"noticias": noticias})


def noticia_detalle(request, junta_slug, slug):
    junta = _junta(request, junta_slug)
    noticia = get_object_or_404(Noticia, junta=junta, slug=slug, publicada=True)
    return render(request, "sitio/noticia_detalle.html", {"noticia": noticia})


def eventos_lista(request, junta_slug):
    junta = _junta(request, junta_slug)
    eventos = Evento.objects.filter(junta=junta, publicado=True)
    return render(request, "sitio/eventos_lista.html", {"eventos": eventos})


def evento_detalle(request, junta_slug, slug):
    junta = _junta(request, junta_slug)
    evento = get_object_or_404(Evento, junta=junta, slug=slug, publicado=True)
    return render(request, "sitio/evento_detalle.html", {"evento": evento})


@require_http_methods(["GET", "POST"])
def certificado(request, junta_slug):
    junta = _junta(request, junta_slug)
    error = ""
    if request.method == "POST":
        ip = ip_cliente(request)
        if exceso_intentos(ip, "certificado"):
            error = "Demasiados intentos. Espera unos minutos e inténtalo de nuevo."
        else:
            certificado_obj, error = emitir_certificado_web(junta, request.POST.get("rut", ""), ip)
            if certificado_obj:
                pdf = pdf_de_certificado(certificado_obj)
                response = HttpResponse(pdf, content_type="application/pdf")
                response["Content-Disposition"] = (
                    f'attachment; filename="certificado-{certificado_obj.codigo}.pdf"'
                )
                return response
    return render(request, "sitio/certificado.html", {"error": error})


def transparencia(request, junta_slug):
    junta = _junta(request, junta_slug)
    gastos = RendicionGasto.objects.filter(junta=junta, publicada=True)
    actividades = InformeActividad.objects.filter(junta=junta, publicada=True)
    total = sum(g.monto for g in gastos)
    return render(
        request,
        "sitio/transparencia.html",
        {"gastos": gastos, "actividades": actividades, "total_gastos": total},
    )


def contacto(request, junta_slug):
    _junta(request, junta_slug)
    return render(request, "sitio/contacto.html")


@require_http_methods(["GET", "POST"])
def verificar_form(request):
    error = ""
    if request.method == "POST":
        codigo = (request.POST.get("codigo") or "").strip().upper()
        if not codigo:
            error = "Ingresa el código impreso en el certificado."
        else:
            return redirect("verificar_detalle", codigo=codigo)
    return render(request, "sitio/verificar.html", {"error": error})


def verificar_detalle(request, codigo: str):
    certificado_obj = Certificado.objects.select_related("junta", "vecino").filter(codigo=codigo.upper()).first()
    return render(
        request,
        "sitio/verificar_detalle.html",
        {"certificado": certificado_obj, "codigo": codigo.upper()},
    )
