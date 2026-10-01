from dataclasses import dataclass
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from contenido.models import Evento, Noticia, SlideCarrusel
from vecinos.models import Vecino
from vecinos.services import cumple_en_rango


@dataclass
class SlideVista:
    tipo: str
    titulo: str
    texto: str
    imagen_url: str | None
    enlace: str | None
    etiqueta: str


def slides_home(junta) -> list[SlideVista]:
    hoy = timezone.localdate()
    ahora = timezone.now()
    items: list[SlideVista] = []

    vecinos = Vecino.objects.filter(junta=junta, activo=True, mostrar_cumpleanos=True)
    for vecino in vecinos:
        if not cumple_en_rango(vecino.fecha_nacimiento, hoy, dias=7):
            continue
        es_hoy = (
            vecino.fecha_nacimiento
            and vecino.fecha_nacimiento.month == hoy.month
            and vecino.fecha_nacimiento.day == hoy.day
        )
        items.append(
            SlideVista(
                tipo="cumple",
                titulo="¡Cumpleaños en el barrio!",
                texto=(
                    f"Hoy cumple años {vecino.nombre_publico_cumple}"
                    if es_hoy
                    else f"Esta semana cumple {vecino.nombre_publico_cumple}"
                ),
                imagen_url=None,
                enlace=None,
                etiqueta="Cumpleaños",
            )
        )

    proximos = Evento.objects.filter(
        junta=junta,
        publicado=True,
        fecha_inicio__gte=ahora - timedelta(hours=2),
        fecha_inicio__lte=ahora + timedelta(days=21),
    )[:4]
    for evento in proximos:
        items.append(
            SlideVista(
                tipo="evento",
                titulo=evento.titulo,
                texto=evento.fecha_inicio.astimezone().strftime("%d/%m %H:%M")
                + (f" · {evento.lugar}" if evento.lugar else ""),
                imagen_url=evento.foto_principal.url if evento.foto_principal else None,
                enlace=reverse("evento_detalle", args=[junta.slug, evento.slug]),
                etiqueta="Evento",
            )
        )

    destacadas = Noticia.objects.filter(junta=junta, publicada=True, destacada=True)[:4]
    for noticia in destacadas:
        items.append(
            SlideVista(
                tipo="noticia",
                titulo=noticia.titulo,
                texto=noticia.bajada,
                imagen_url=noticia.foto_principal.url if noticia.foto_principal else None,
                enlace=reverse("noticia_detalle", args=[junta.slug, noticia.slug]),
                etiqueta="Noticia",
            )
        )

    for slide in SlideCarrusel.objects.filter(junta=junta, activo=True):
        if slide.desde and hoy < slide.desde:
            continue
        if slide.hasta and hoy > slide.hasta:
            continue
        items.append(
            SlideVista(
                tipo="manual",
                titulo=slide.titulo,
                texto=slide.texto,
                imagen_url=slide.imagen.url if slide.imagen else None,
                enlace=slide.enlace or None,
                etiqueta="Destacado",
            )
        )

    return items[:8]
