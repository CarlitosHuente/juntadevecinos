from copy import deepcopy

BLOQUES = (
    ("encabezado", "Encabezado"),
    ("logo", "Logo"),
    ("titulo", "Título"),
    ("cuerpo", "Subtítulo / fecha"),
    ("caja", "Datos del socio"),
    ("detalle", "Detalle de pagos"),
    ("pie", "Pie de página"),
)

LAYOUT_DEFAULT = {
    "pagina": {"bg": "#FFFFFF"},
    "encabezado": {
        "x": 0, "y": 0, "w": 21, "h": 3.6, "z": 1, "font": 13, "align": "left", "fit": True,
        "bg": "#2D8A4E", "color": "#FFFFFF", "pad": 0.55, "padL": 4.6, "radius": 0,
    },
    "logo": {
        "x": 1.5, "y": 0.5, "w": 2.6, "h": 2.6, "z": 8, "font": 12, "align": "center", "fit": False,
        "bg": "", "color": "#1F2A1F", "zoom": 1, "panX": 0, "panY": 0, "pad": 0, "padL": 0, "radius": 0,
    },
    "titulo": {
        "x": 1.8, "y": 4.4, "w": 17.4, "h": 1.6, "z": 2, "font": 20, "align": "left", "fit": True,
        "bg": "", "color": "#1F2A1F", "pad": 0.15, "padL": 0.15, "radius": 0,
    },
    "cuerpo": {
        "x": 1.8, "y": 6.1, "w": 17.4, "h": 1.1, "z": 3, "font": 12, "align": "left", "fit": True,
        "bg": "", "color": "#4B5563", "pad": 0.1, "padL": 0.15, "radius": 0,
    },
    "caja": {
        "x": 1.8, "y": 7.6, "w": 17.4, "h": 3.6, "z": 4, "font": 12, "align": "left", "fit": True,
        "bg": "#F8FAF8", "color": "#1F2A1F", "pad": 0.4, "padL": 0.45, "radius": 0.12,
    },
    "detalle": {
        "x": 1.8, "y": 11.8, "w": 17.4, "h": 11.4, "z": 5, "font": 12, "align": "left", "fit": True,
        "bg": "", "color": "#1F2A1F", "pad": 0.2, "padL": 0.2, "radius": 0,
    },
    "pie": {
        "x": 0, "y": 27.6, "w": 21.0, "h": 2.1, "z": 6, "font": 9, "align": "left", "fit": True,
        "bg": "#2D8A4E", "color": "#FFFFFF", "pad": 0.4, "padL": 0.8, "radius": 0,
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
    return base
