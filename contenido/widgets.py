from django import forms


class RecorteImagenWidget(forms.ClearableFileInput):
    template_name = "admin/widgets/recorte_imagen.html"
    accept = "image/*"

    def __init__(self, ratio="16/10", etiqueta="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ratio = ratio
        self.etiqueta = etiqueta

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        attrs.setdefault("accept", "image/*")
        attrs["class"] = f"{attrs.get('class', '')} recorte-input".strip()
        attrs["data-recorte"] = "1"
        attrs["data-ratio"] = self.ratio
        attrs["data-etiqueta"] = self.etiqueta
        if value and getattr(value, "url", None):
            attrs["data-inicial"] = value.url
        context = super().get_context(name, value, attrs)
        context["widget"]["ratio"] = self.ratio
        context["widget"]["etiqueta"] = self.etiqueta
        return context


class RecorteImagenMixin:
    recorte_campos = {}

    class Media:
        css = {"all": ("css/recorte-imagen.css",)}
        js = ("js/recorte-imagen.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        campo = super().formfield_for_dbfield(db_field, request, **kwargs)
        cfg = self.recorte_campos.get(db_field.name)
        if campo and cfg:
            campo.widget = RecorteImagenWidget(
                ratio=cfg.get("ratio", "16/10"),
                etiqueta=cfg.get("etiqueta", "Así se verá en el sitio"),
            )
        return campo
