# 07 · Despliegue

> **En producción desde 2026‑11‑15: https://nasa.cardenal-shekers.online** (D17)

## 1. Situación actual del servidor (revisada el 2026‑11‑15)
- **agui-server:** Ubuntu, 4 CPU, 3.6 GB de RAM con unos 2 GB disponibles y swap ya en uso, 394 GB de disco libre, Docker 29.
- **Cloudflare Tunnel** activo (servicio `cloudflared`). La ruta actual es `cardenal-shekers.online` → `http://localhost:80`, que es el contenedor `rrhh_frontend`, el sistema RRHH de `/home/aguilar/Data-analyst-competency-UPQ`.
- La sesión tmux **`catch`** es otra sesión de Claude Code que trabaja ahora mismo sobre ese sistema RRHH.
- Existe `~/.cloudflared/cert.pem`, así que se pueden **crear nuevos subdominios** del mismo túnel sin tocar el sitio actual.

## 2. Opciones para publicar
| Opción | Qué implica | Ventaja | Desventaja |
|---|---|---|---|
| **A. Subdominio** (recomendada), p. ej. `marine.cardenal-shekers.online` | Agregar una regla `ingress` al túnel y un CNAME (`cloudflared tunnel route dns`). Reiniciar `cloudflared`, con un corte de segundos. | **RRHH sigue funcionando.** No hay downtime ni conflicto con la sesión `catch`. | Requiere `sudo` para editar `/etc/cloudflared/config.yml` |
| B. Reemplazar el dominio raíz (lo que autorizaste) | Bajar `rrhh_frontend` y apuntar `cardenal-shekers.online` al dashboard | URL más corta | RRHH queda fuera de línea mientras tanto, y la otra sesión de Claude podría volver a levantarlo |
| C. Streamlit Community Cloud | Repo público, app gratuita | Cero mantenimiento | Sin worker programado ni disco persistente, 1 GB de RAM y suspensión por inactividad. **No sirve para el monitoreo NRT.** |

**Decisión aprobada (D09): opción A, subdominio.** Logra el objetivo, que el sitio sea público en tu dominio, sin bajar el otro servicio. La opción B solo aporta una URL más corta a cambio de tumbar un sistema en uso. **No se hará ningún cambio en cloudflared ni en RRHH sin tu confirmación explícita en ese momento.**

## 3. Topología implementada (D17)

Se implementó la opción A con una mejora: en lugar de editar `/etc/cloudflared/config.yml`, que requiere `sudo` y es la configuración de RRHH, el proyecto tiene **su propio túnel** (`mece-nasa`) que corre como contenedor. RRHH no se tocó.

```
Internet ─HTTPS─► Cloudflare ─┬─ túnel tunel-nginx (systemd, RRHH) ─► cardenal-shekers.online → localhost:80
                              └─ túnel mece-nasa  (Docker, proyecto) ─► nasa.cardenal-shekers.online → app:8501

docker compose (proyecto "mece", docker/docker-compose.yml)
  mece_app      Streamlit          127.0.0.1:8502   mem_limit 768m
  mece_tunnel   cloudflared        (sin puertos)    mem_limit 128m
  mece_worker   pipeline de datos  perfil "worker"  mem_limit 1g
  volumen       ../data  (bind mount, persistente)
```

### Operación
```bash
./docker/deploy.sh            # construye y levanta app + túnel
./docker/deploy.sh worker     # además el worker (actualización cada 6 h)
docker compose --env-file .env -f docker/docker-compose.yml logs -f app
```
- El `Dockerfile` instala las dependencias en una capa cacheable, así que un cambio de código redespliega en unos 80 s.
- Las credenciales van en `.env`, nunca en el repositorio: `EARTHDATA_TOKEN` y `CF_CREDENTIALS_FILE` (credenciales del túnel en `~/.cloudflared/`).
- El ID del túnel aparece en `docker/cloudflared/config.yml`. No es secreto, porque ya es visible en el CNAME público.

### Lecciones del despliegue
- `cloudflared tunnel route dns` lee `~/.cloudflared/config.yml` (túnel de RRHH) aunque se le indique otro túnel. Hay que usar `--config` con un archivo que solo contenga `origincert`.
- netCDF4/HDF5 no es seguro entre hilos: toda E/S NetCDF del pipeline pasa por un candado (`NC_LOCK`).
- La primera visita tras un redespliegue tarda ~10 s, porque importa las bibliotecas científicas y construye el globo. Las siguientes tardan ~1 s.

## 4. GitHub
- Repositorio sin marca de herramientas de IA: sin líneas de coautoría automática, sin `CLAUDE.md` y sin la carpeta `.claude/`, que ya están en `.gitignore`.
- **Falta definir** (ver `decisiones.md`):
  - la URL u organización del repositorio;
  - el método de autenticación desde el servidor, ya que hoy no hay llave SSH registrada en GitHub ni `gh` instalado;
  - el nombre y correo con que se firman los commits.
