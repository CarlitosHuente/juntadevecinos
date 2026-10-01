from django import forms

SWATCHES = (
    ("#2D8A4E", "Verde junta"),
    ("#1B5E3B", "Verde oscuro"),
    ("#0F766E", "Verde agua"),
    ("#F4C430", "Mostaza"),
    ("#E8A317", "Ámbar"),
    ("#C45C26", "Terracota"),
    ("#3A8FCD", "Azul apoyo"),
    ("#1D4ED8", "Azul"),
    ("#7C3AED", "Violeta"),
    ("#B91C1C", "Rojo"),
    ("#111827", "Negro"),
    ("#6B7280", "Gris"),
)


def _hex(valor: str, fallback: str = "#2D8A4E") -> str:
    texto = (valor or "").strip()
    if not texto.startswith("#"):
        texto = f"#{texto}"
    if len(texto) == 7 and all(c in "0123456789abcdefABCDEF#" for c in texto):
        return texto.upper()
    return fallback


class ColorPaletaWidget(forms.TextInput):
    template_name = "admin/widgets/color_paleta.html"

    class Media:
        css = {"all": ("css/color-paleta.css",)}
        js = ("js/color-paleta.js",)

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        attrs.setdefault("maxlength", "7")
        attrs.setdefault("spellcheck", "false")
        attrs["class"] = f"{attrs.get('class', '')} color-paleta-hex".strip()
        context = super().get_context(name, value, attrs)
        context["widget"]["hex"] = _hex(value)
        context["widget"]["swatches"] = SWATCHES
        return context
