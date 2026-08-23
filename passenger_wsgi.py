import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTERP = os.environ.get(
    "PYTHON_INTERP",
    os.path.join(BASE_DIR, ".venv", "bin", "python"),
)

if INTERP and os.path.exists(INTERP) and sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
