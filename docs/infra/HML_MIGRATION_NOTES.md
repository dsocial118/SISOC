# HML - Notas iniciales de migracion

Estado: inventario de migracion actualizado el 2026-07-13. No autoriza una
migracion. La fuente canonica es `hml-old`; AWS queda fuera de alcance.

## Que habria que copiar o recrear

| Elemento | Tratamiento |
| --- | --- |
| `/sisoc/SISOC/media` | Copia de 48 GiB/45,303 archivos con timestamps, conteo y checksums |
| Backend SISOC | Clonar branch/commit aprobado; no tar del working tree historico |
| SISOC-Mobile | Clonar repo/commit aprobado y recrear su configuracion local |
| `.env` backend/mobile | Transferir por canal seguro; nunca versionar ni imprimir valores |
| DB `10.80.5.48` | Backup consistente y restore probado, coordinado con el host DB |
| NGINX | Config, dominios, aliases, proxies, logs y metadata de certificados |
| TLS | Emitir/instalar certificado valido; no reutilizar una key sin politica aprobada |
| Runner | Reinstalar y registrar runner nuevo con label `sisoc-homologacion` |
| Cron/timers | Exportar estado efectivo root/`sisoc-deploy`, no solo `scripts/crontab` |
| Logs | Copiar solo si existe requisito legal u operativo |

No copiar como runtime por defecto:

- `/var/www/SISOC` ni `/opt/ssies/SISOC-Backoffice-deprecated`;
- imagenes/build cache Docker, si pueden reconstruirse desde commits;
- `static_root`, que se regenera;
- credenciales persistentes del runner viejo;
- MySQL local: Stage 1 aplicado, sin schemas/dependencias; no migrarlo como DB
  canonica. Conservar temporalmente el backup y metadata para rollback.

## Que habria que reinstalar/configurar

- SO soportado, Git, Docker Engine y Compose compatibles.
- NGINX con 80/443, redirects, `/static`, `/media`, `/mobile` y backend.
- Backend Django/OCR desde `/sisoc/SISOC` o un path nuevo documentado.
- Frontend SISOC-Mobile desde su repo y compose.
- DB separada, ACL limitada, backup, retencion y monitoreo.
- Certificado valido con un unico mecanismo autoritativo de renovacion.
- Usuario operativo, runner, cron, logrotate y monitoreo.
- Capacidad para al menos media actual, crecimiento, builds y rollback.

No igualar versiones a QA por estetica. Mantener las versiones HML actuales o
elegir otras solo mediante un cambio aprobado y probado.

## Secretos a transferir por canal seguro

- Django secret/configuracion de hosts y origins.
- Credenciales MySQL.
- GESTIONAR y RENAPER.
- Sentry, email y cualquier integracion externa.
- Configuracion no publica de SISOC-Mobile, si se incorpora en el futuro.
- Deploy keys y token efimero de registro del runner.
- Clave privada TLS solo si la politica decide transferirla; preferir emision
  nueva cuando corresponda.

## Servicios a levantar

Orden conceptual:

1. red, firewall, DNS y DB restaurada/validada;
2. Docker/containerd;
3. backend Django y OCR, con side effects de DB expresamente aprobados;
4. SISOC-Mobile;
5. NGINX y TLS;
6. cron, monitoreo y logs;
7. runner self-hosted, despues de validar el runtime manualmente.

## Validaciones minimas del destino

```bash
hostnamectl
df -hT /
df -ih /
systemctl is-active docker containerd nginx cron
git -C "$APP_ROOT" branch --show-current
git -C "$APP_ROOT" rev-parse HEAD
GIT_OPTIONAL_LOCKS=0 git -C "$APP_ROOT" status --short --branch
docker compose -f "$APP_ROOT/docker-compose.deploy.yml" ps
docker compose -f "$MOBILE_ROOT/compose.prod.yaml" ps
nginx -t
ss -lntup
curl --max-time 8 -fsS "https://hml-sisoc.secretarianaf.gob.ar/health/"
curl --max-time 8 -fsS "https://hml-sisoc.secretarianaf.gob.ar/mobile/"
```

La validacion TLS no debe usar `-k`. Agregar:

- consulta DB read-only desde Django;
- login autorizado y pagina con datos;
- static y un archivo media existente;
- conteo/checksum de media;
- frontend movil y su comunicacion con backend;
- worker OCR estable sin disparar un job real no aprobado;
- certificado/cadena/renovacion;
- logs locales sin errores nuevos ni copia de PII;
- backup y restore documentados.

## Rollback conceptual

- conservar HML viejo operativo hasta cerrar el cutover;
- registrar commits backend/mobile antes y despues;
- conservar backup DB restaurable y copia verificada de media;
- preparar rollback de DNS/ruta y certificado;
- no usar un deploy como rollback automatico porque reinicia y escribe DB;
- si falla, devolver trafico al host anterior y preservar evidencia.

## Pendientes antes de un checklist final

1. Backup/restore de DB `10.80.5.48`.
2. Backup y crecimiento de media.
3. Cierre de observacion del Stage 1 MySQL despues del 2026-07-20.
4. Certificado valido y mecanismo de renovacion.
5. Cron root, firewall y puertos 10000/10050.
6. Flujo de deploy/rollback de SISOC-Mobile.
7. Decision sobre checkouts y servicios historicos.
