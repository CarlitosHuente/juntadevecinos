from django.urls import path

from sitio import views

urlpatterns = [
    path("", views.home, name="home"),
    path("quienes-somos/", views.quienes_somos, name="quienes_somos"),
    path("noticias/", views.noticias_lista, name="noticias_lista"),
    path("noticias/<slug:slug>/", views.noticia_detalle, name="noticia_detalle"),
    path("eventos/", views.eventos_lista, name="eventos_lista"),
    path("eventos/<slug:slug>/", views.evento_detalle, name="evento_detalle"),
    path("certificado/", views.certificado, name="certificado"),
    path("transparencia/", views.transparencia, name="transparencia"),
    path("contacto/", views.contacto, name="contacto"),
]
