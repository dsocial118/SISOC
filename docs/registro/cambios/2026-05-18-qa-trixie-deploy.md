# Deploy QA Debian 13

Se documenta el procedimiento operativo para desplegar QA en Debian GNU/Linux 13 con dos servidores:

- SITE-QA: Django/SISOC + NGINX en `10.1.131.121`.
- DB-QA: MySQL 8.0 dedicado en `10.1.130.88`.

La decision operativa es mantener QA simple con Docker Compose, NGINX y firewall:

- SITE-QA usa branch `development` y `docker-compose.deploy.yml`.
- DB-QA usa un compose dedicado fuera del repo en `/opt/sisoc-mysql/compose.yml`.
- No se usa `docker-compose.site.yml`.
- No se usa `docker-compose.yml` para deploy.
- Los secretos reales no se versionan; el runbook usa placeholders y advierte no ejecutar `source .env`.
