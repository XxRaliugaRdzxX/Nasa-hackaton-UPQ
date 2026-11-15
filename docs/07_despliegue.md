# 07 · Propuesta de despliegue

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

## 3. Topología
```
Internet ──HTTPS──► Cloudflare ──túnel──► cloudflared (host)
                                            ├─ cardenal-shekers.online        → localhost:80   (RRHH, sin cambios)
                                            └─ marine.cardenal-shekers.online → localhost:8502 (mece-app)

docker compose (proyecto "mece")
  mece-app     Streamlit   127.0.0.1:8502   mem_limit 768m   lectura de /data
  mece-worker  supercronic                  mem_limit 1g     escritura de /data
  volumen      ./data  (bind mount, persistente, respaldable)
```
- El puerto 8502 se publica solo en `127.0.0.1`, así que no se expone directamente a Internet.
- Las credenciales de Earthdata van en `.env`, solo dentro de `mece-worker`. La app no las necesita.
- Respaldo: un `tar` diario de `data/processed`, `data/spatial` y `data/catalog`, que pesa menos de 1 GB. `data/raw` se puede regenerar.

## 4. GitHub
- Repositorio sin marca de herramientas de IA: sin líneas de coautoría automática, sin `CLAUDE.md` y sin la carpeta `.claude/`, que ya están en `.gitignore`.
- **Falta definir** (ver `decisiones.md`):
  - la URL u organización del repositorio;
  - el método de autenticación desde el servidor, ya que hoy no hay llave SSH registrada en GitHub ni `gh` instalado;
  - el nombre y correo con que se firman los commits.
