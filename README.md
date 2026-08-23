# Juntas de vecinos

Sitio web para juntas de vecinos: información del barrio, noticias, eventos y **certificados de residencia en PDF** con código y QR para verificar que no fueron adulterados.

Primera junta: **Huente**, en `/huente/`. El modelo admite más juntas después (`/otra-junta/`).

Este repositorio es independiente. No comparte código ni remoto con otros proyectos.

## Requisitos locales

- Python 3.12
- En producción: MySQL 8 (phpMyAdmin en HostingChile)

## Arranque local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py sembrar_huente
python manage.py runserver
```

Abre http://127.0.0.1:8000/ (redirige a `/huente/`).

Usuarios de ejemplo (solo desarrollo; cámbialos en producción):

| Usuario       | Contraseña | Rol          |
| ------------- | ---------- | ------------ |
| `admin`       | `admin1234` | Superadmin  |
| `directiva`   | `huente1234` | Directiva  |
| `comunicador` | `huente1234` | Comunicador |
| `secretario`  | `huente1234` | Secretario |

Panel: http://127.0.0.1:8000/admin/

RUT de prueba para certificado: `12.345.678-5`

## Roles

Cada perfil entra a `/admin/` y solo ve lo suyo:

- **Superadmin:** juntas, usuarios y todo el sistema.
- **Directiva:** sede, usuarios de su junta, vecinos, contenido y certificados.
- **Comunicador:** noticias con imagen, eventos y slides del carrusel.
- **Secretario:** nómina de vecinos y consulta/anulación de certificados.

Los vecinos no tienen cuenta: ingresan su RUT en `/huente/certificado/`.

## Certificados

1. El vecino ingresa un RUT vigente.
2. Se genera un PDF con código (ej. `HU-A9K2-7M4Q`) y QR.
3. Cualquiera verifica en `/verificar/CODIGO/`.
4. Si el PDF se edita, el verificador sigue mostrando los datos oficiales del servidor.

## Despliegue en HostingChile (cPanel + GitHub)

1. En cPanel → **MySQL Databases**, crea la base y el usuario. Puedes revisar tablas en phpMyAdmin.
2. Copia `.env.example` a `.env` (o usa Variables de entorno de Python App) y completa:

   ```
   DEBUG=False
   SECRET_KEY=una-clave-larga-y-secreta
   ALLOWED_HOSTS=tudominio.cl,www.tudominio.cl
   CSRF_TRUSTED_ORIGINS=https://tudominio.cl,https://www.tudominio.cl
   SITE_URL=https://tudominio.cl
   MYSQL_NAME=usuario_juntas
   MYSQL_USER=usuario_juntas
   MYSQL_PASSWORD=...
   MYSQL_HOST=localhost
   PYTHON_INTERP=/home/USUARIO/virtualenv/juntadevecinos/3.12/bin/python
   ```

3. En cPanel → **Git Version Control**, clona este repositorio privado.
4. En **Setup Python App**, Python 3.12, archivo de arranque `passenger_wsgi.py`.
5. Instala dependencias: `pip install -r requirements.txt`.
6. En la carpeta del proyecto:

   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

7. Asegura que `media/` se pueda escribir (logos y fotos de noticias).
8. Reinicia la aplicación Python.

El vecino pide el certificado sin login. El comunicador publica artículos desde su usuario.

## Licencia

Uso de la junta. Ajusta el dominio y los datos de contacto antes de publicar.
