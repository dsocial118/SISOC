# Runbook generico de entornos

Se agrega una plantilla operativa generica para replicar SISOC en QA, homologacion o produccion usando:

- SITE dedicado para Django/SISOC + NGINX.
- DB dedicada con MySQL 8.0.
- `docker-compose.deploy.yml` como compose base de aplicacion.
- `docker-compose.produccion.yml` solo cuando el entorno lo requiera.
- Compose operativo de MySQL fuera del repo, bajo `/opt/sisoc-mysql`.

El runbook de QA queda como ejemplo aplicado a Debian 13 trixie, mientras que `deploy_entornos_docker_nginx_mysql.md` contiene los parametros y comandos reutilizables para otros entornos.
