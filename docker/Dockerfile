# Imagen única para la app (Streamlit) y el worker (pipeline de datos)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MECE_ROOT=/app \
    MECE_DATA_DIR=/app/data

WORKDIR /app

# Bibliotecas del sistema que necesitan las ruedas de rasterio/GDAL
RUN apt-get update \
 && apt-get install -y --no-install-recommends libexpat1 \
 && rm -rf /var/lib/apt/lists/*

# 1) Dependencias (capa cacheable): se instala el proyecto con un paquete vacío, así un
#    cambio de código no obliga a reinstalar todo. requirements.txt fija las versiones.
COPY pyproject.toml README.md LICENSE requirements.txt ./
RUN mkdir -p src/mece && touch src/mece/__init__.py \
 && pip install -c requirements.txt ".[dashboard]" \
 && rm -rf src
# 2) Código del paquete (rápido, sin dependencias)
COPY src ./src
RUN pip install --no-deps --force-reinstall .

COPY config ./config
COPY dashboard ./dashboard

# HTML inicial de Streamlit (se ve antes de que cargue la app y en vistas previas de enlaces):
# título y favicon del proyecto en lugar de "Streamlit"
RUN ST=$(python -c "import streamlit, os; print(os.path.dirname(streamlit.__file__))")/static \
 && sed -i 's|<title>Streamlit</title>|<title>NASA Space Apps</title>|' "$ST/index.html" \
 && cp dashboard/assets/favicon.png "$ST/favicon.png" \
 && sed -i 's|href="./favicon.png"|href="./favicon.png?v=2"|' "$ST/index.html"
# ?v=2: Cloudflare cachea /favicon.png un año (immutable); cambiar la versión fuerza el nuevo ícono
COPY .streamlit ./.streamlit
COPY docker/worker.sh ./docker/worker.sh

# Mismo UID que el usuario del servidor para escribir en el volumen de datos
RUN useradd --uid 1000 --create-home mece && mkdir -p /app/data && chown -R mece:mece /app
USER mece

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4)"

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
