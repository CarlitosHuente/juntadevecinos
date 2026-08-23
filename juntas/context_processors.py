def junta_actual(request):
    return {"junta": getattr(request, "junta", None)}
