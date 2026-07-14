# HML - Checklist de migracion

Fuente canonica actual: `hml-old`. Los hosts AWS son referencias de una
migracion futura y no forman parte del entorno vigente.

## Antes de migrar

- [ ] Registrar branch/commit backend `homologacion` y mobile `main`.
- [x] DB real confirmada: `10.80.5.48:3306`, schema `sisoc_local`.
- [x] MySQL local retirado en Stage 1; no tratarlo como DB canonica.
- [ ] Crear backup consistente de DB y probar restore aislado.
- [ ] Copiar 48 GiB de `media/` preservando estructura y verificar checksums.
- [ ] Transferir ambos `.env` por canal seguro; nunca versionar valores.
- [ ] Exportar NGINX, runner/systemd, crontabs y scripts operativos.
- [ ] Registrar versiones de SO, Docker, Compose, NGINX e imagenes.
- [ ] Confirmar firewall/ACL, incluidos 22, 80/443, 8001, 8080 y DB remota.
- [ ] Definir DNS/TLS y rollback de trafico.

## Reinstalar/configurar

- [ ] Usuario operativo y acceso Docker minimo.
- [ ] Docker Engine y Compose compatibles; no igualar versiones a QA por estetica.
- [ ] NGINX con redirects, static/media, backend y `/mobile/`.
- [ ] Backend/OCR desde un checkout limpio del commit aprobado.
- [ ] SISOC-Mobile desde un checkout limpio del commit aprobado.
- [ ] Runner nuevo con label `sisoc-homologacion`; no copiar sus credenciales.
- [ ] Cron de mantenimiento con umbral 80%, retencion 14 dias y sin volumenes.
- [ ] Monitoreo de disco, health, logs y crecimiento de media.
- [ ] DB separada con ACL, backup, retencion y restore probado.

## No copiar como fuente primaria

- MySQL local, su datadir o paquetes.
- `/var/www/SISOC` y `/opt/ssies/SISOC-Backoffice-deprecated`.
- `static_root/`, imagenes y build cache Docker regenerables.
- dumps locales antiguos o credenciales persistentes del runner.
- logs salvo requisito operativo/legal definido.

## Cutover y validacion

- [ ] Autorizar los side effects del entrypoint antes del primer `up`.
- [ ] Levantar DB/red, backend/OCR, mobile y finalmente NGINX.
- [ ] Confirmar tres contenedores activos y mobile healthy.
- [ ] Confirmar HTTPS valido en `/`, `/health/` y `/mobile/`, sin `-k`.
- [ ] Probar login/pagina con datos mediante un usuario HML autorizado.
- [ ] Validar static y un media existente.
- [ ] Comparar conteo/checksum de media.
- [ ] Revisar logs localmente sin copiar secretos/PII.
- [ ] Confirmar cron, runner y deploy controlado.

## Rollback de migracion

- [ ] Mantener `hml-old` disponible y sin cambios hasta cerrar el cutover.
- [ ] Conservar backup DB validado y copia verificada de media.
- [ ] Registrar commits previos/nuevos y mecanismo para devolver trafico.
- [ ] Si falla, detener el destino y devolver trafico; no restaurar parcialmente
      sobre la DB fuente sin un plan aprobado.
