# QA - Checklist de migracion

Fuente canonica actual: `qa-old`. Los hosts AWS son referencias de una migracion
futura y no forman parte de esta auditoria.

## Antes de migrar

- [ ] Registrar branch `development`, commit y estado del working tree.
- [x] Host/schema DB real confirmado: `10.80.9.18:3306`, `sisoc_local`.
- [ ] Crear backup consistente de DB y probar restore en un destino aislado.
- [ ] Copiar `media/` preservando estructura y verificar conteo/checksums.
- [ ] Transferir `.env` por canal seguro; nunca versionarlo ni imprimir valores.
- [ ] Exportar NGINX, runner/systemd, crontab y scripts operativos.
- [ ] Registrar versiones de SO, Docker, Compose, NGINX, MySQL e imagen Python.
- [ ] Confirmar ACL/firewall de 22, 80/443, 8001 y 3306.
- [ ] Definir hostname/DNS/TLS y rollback de red.

## Reinstalar/configurar

- [ ] Usuario `sisoc-deploy` y acceso Docker minimo.
- [ ] Docker Engine y Compose compatibles.
- [ ] NGINX con aliases de static/media y proxy a 8001.
- [ ] Checkout limpio en el commit aprobado.
- [ ] Runner nuevo con label `sisoc-qa`; no copiar credenciales persistentes del
      runner anterior.
- [ ] Cron de mantenimiento de disco con umbral 80% y retencion 14 dias.
- [ ] Monitoreo y alertas de disco/health.
- [ ] MySQL en el host definido, limitado por red y con backup/retencion.

## No copiar como fuente primaria

- `static_root/`: se regenera.
- imagenes y build cache Docker: reconstruir desde el Dockerfile.
- dumps locales antiguos: no usarlos; los dos detectados fueron eliminados con
  aprobacion.
- credenciales internas del runner.
- el working tree completo si Git puede reproducir el commit.

## Cutover y validacion

- [ ] Autorizar los side effects del entrypoint antes del primer `up`.
- [ ] Levantar Docker/Compose y luego NGINX.
- [ ] Confirmar ambos contenedores activos.
- [ ] Confirmar HTTP 200 en `/` y `/health/`.
- [ ] Probar una pagina que consulte DB con un usuario QA autorizado.
- [ ] Validar static y un media existente.
- [ ] Revisar logs localmente sin copiar secretos/PII.
- [ ] Confirmar cron, runner y deploy controlado.

## Rollback de migracion

- [ ] Mantener `qa-old` disponible y sin cambios hasta cerrar el cutover.
- [ ] Conservar backup DB validado y copia verificada de media.
- [ ] Registrar commit previo/nuevo y mecanismo para devolver trafico.
- [ ] Si falla, detener el destino y devolver trafico; no improvisar una
      restauracion parcial sobre la DB fuente.
