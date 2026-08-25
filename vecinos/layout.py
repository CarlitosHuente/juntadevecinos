from copy import deepcopy

BLOQUES = (
    ("encabezado", "Encabezado"),
    ("logo", "Logo"),
    ("titulo", "Título"),
    ("cuerpo", "Cuerpo"),
    ("caja", "Caja de datos"),
    ("qr", "Código QR"),
    ("verificacion", "Verificación"),
    ("pie", "Pie de página"),
)

LAYOUT_DEFAULT = {
    "pagina": {"bg": "#FFFFFF"},
    "encabezado": {
        "x": 0, "y": 0, "w": 21, "h": 3.4, "z": 1, "font": 14, "align": "left", "fit": True,
        "bg": "#2D8A4E", "color": "#FFFFFF", "pad": 0.4, "padL": 4.5, "radius": 0,
    },
    "logo": {
        "x": 1.6, "y": 0.5, "w": 2.6, "h": 2.6, "z": 8, "font": 12, "align": "center", "fit": False,
        "bg": "", "color": "#1F2A1F", "zoom": 1, "panX": 0, "panY": 0, "pad": 0, "padL": 0, "radius": 0,
    },
    "titulo": {
        "x": 2.0, "y": 4.3, "w": 17.0, "h": 1.5, "z": 2, "font": 18, "align": "center", "fit": True,
        "bg": "", "color": "#1F2A1F", "pad": 0.12, "padL": 0.12, "radius": 0,
    },
    "cuerpo": {
        "x": 2.2, "y": 6.1, "w": 16.6, "h": 5.2, "z": 3, "font": 12, "align": "justify", "fit": True,
        "bg": "", "color": "#1F2A1F", "pad": 0.12, "padL": 0.12, "radius": 0,
    },
    "caja": {
        "x": 2.0, "y": 12.0, "w": 17.0, "h": 5.0, "z": 4, "font": 11, "align": "left", "fit": True,
        "bg": "#F4F1E8", "color": "#1F2A1F", "pad": 0.28, "padL": 0.35, "radius": 0.15,
    },
    "qr": {
        "x": 15.2, "y": 12.35, "w": 3.4, "h": 3.4, "z": 9, "font": 10, "align": "center", "fit": False,
        "bg": "#FFFFFF", "color": "#1F2A1F", "pad": 0.08, "padL": 0.08, "radius": 0,
    },
    "verificacion": {
        "x": 2.2, "y": 23.6, "w": 16.6, "h": 2.6, "z": 5, "font": 9, "align": "left", "fit": True,
        "bg": "", "color": "#3A4A3A", "pad": 0.12, "padL": 0.12, "radius": 0,
    },
    "pie": {
        "x": 0, "y": 28.1, "w": 21.0, "h": 1.6, "z": 6, "font": 9, "align": "center", "fit": True,
        "bg": "#2D8A4E", "color": "#FFFFFF", "pad": 0.25, "padL": 0.25, "radius": 0,
    },
}

CAMPOS_NUM = ("x", "y", "w", "h", "z", "font", "zoom", "panX", "panY", "pad", "padL", "radius")
CAMPOS_TXT = ("align", "bg", "color")
CAMPOS_BOOL = ("fit",)


def layout_por_defecto() -> dict:
    return deepcopy(LAYOUT_DEFAULT)


def orden_pintado(layout: dict) -> list[str]:
    claves = [k for k in layout if k != "pagina" and isinstance(layout.get(k), dict)]
    return sorted(claves, key=lambda k: float(layout[k].get("z") or 0))


def layout_completo(diseno) -> dict:
    base = layout_por_defecto()
    junta = getattr(diseno, "junta", None)
    guardado = getattr(diseno, "layout", None) or {}
    if junta:
        primario = junta.color_primario or "#2D8A4E"
        if "bg" not in (guardado.get("encabezado") or {}):
            base["encabezado"]["bg"] = primario
        if "bg" not in (guardado.get("pie") or {}):
            base["pie"]["bg"] = primario
    if isinstance(guardado.get("pagina"), dict) and "bg" in guardado["pagina"]:
        base["pagina"]["bg"] = guardado["pagina"]["bg"]
    for clave, bloque in base.items():
        if clave == "pagina" or not isinstance(guardado.get(clave), dict):
            continue
        src = guardado[clave]
        for k in CAMPOS_NUM:
            if k in src:
                bloque[k] = src[k]
        for k in CAMPOS_TXT:
            if k in src:
                bloque[k] = src[k]
        for k in CAMPOS_BOOL:
            if k in src:
                bloque[k] = src[k]
    if not guardado.get("logo") and getattr(diseno, "logo_x", None) is not None:
        base["logo"].update({
            "x": float(diseno.logo_x),
            "y": float(diseno.logo_y),
            "w": float(diseno.logo_ancho),
            "h": float(diseno.logo_alto),
        })
    return base
