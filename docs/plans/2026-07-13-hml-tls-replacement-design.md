# Reemplazo TLS vencido en HML

Estado: propuesto, bloqueado hasta recibir el certificado wildcard renovado.

## Evidencia

- NGINX usa `/etc/apache2/certs/fullchain.crt` y
  `/etc/apache2/certs/secretarianaf.gob.ar.key`.
- Leaf: `*.secretarianaf.gob.ar`, emisor Sectigo, vencido el 2026-03-06.
- Las copias `.crt`, `.fullchain.pem` y `fullchain.crt` tienen el mismo serial,
  fingerprint, public key y vencimiento.
- La parte publica de la key activa coincide con el leaf.
- El intermedio COMODO vigente no es un certificado leaf y no puede usarse solo.
- Certbot apt y snap no tienen configuraciones `renewal` ni `live`; sus timers no
  administran este certificado.

## Insumo requerido

Infra debe proveer por canal seguro:

1. certificado wildcard renovado para `*.secretarianaf.gob.ar`;
2. cadena/intermedios correctos en orden de fullchain;
3. confirmacion de si fue emitido contra la key actual;
4. si usa una key nueva, la key privada por canal seguro y con politica aprobada.

No guardar certificado/key nuevos en Git. Staging root-only fuera del repo.

## Preflight del material nuevo

Con paths root-only `NEW_FULLCHAIN` y, si corresponde, `NEW_KEY`:

```bash
openssl x509 -in "$NEW_FULLCHAIN" -noout \
  -subject -issuer -dates -serial -fingerprint -sha256 -ext subjectAltName

cert_hash="$({
  openssl x509 -in "$NEW_FULLCHAIN" -noout -pubkey \
    | openssl pkey -pubin -outform DER
} | sha256sum | awk '{print $1}')"

key_hash="$({
  openssl pkey -in "$NEW_KEY" -pubout -outform DER
} | sha256sum | awk '{print $1}')"

test "$cert_hash" = "$key_hash"
```

Validar:

- SAN contiene `*.secretarianaf.gob.ar`;
- fecha actual dentro de vigencia;
- fullchain parseable;
- certificado y key coinciden;
- no imprimir ni copiar el contenido de la key.

Si el certificado renovado usa la key actual, `NEW_KEY` debe apuntar a
`/etc/apache2/certs/secretarianaf.gob.ar.key` y no se reemplaza la key.

## Backup previo

```bash
timestamp="$(date +%Y%m%d_%H%M%S)"
backup="/var/backups/sisoc/tls/hml/$timestamp"
sudo install -d -o root -g root -m 700 "$backup"
sudo cp -a /etc/apache2/certs/fullchain.crt "$backup/"
sudo cp -a /etc/apache2/certs/secretarianaf.gob.ar.key "$backup/"
sudo cp -a /etc/nginx/sites-available/sisoc "$backup/"
sudo sh -c '
  cd "$1"
  sha256sum fullchain.crt secretarianaf.gob.ar.key sisoc > SHA256SUMS
  chmod 600 fullchain.crt secretarianaf.gob.ar.key sisoc SHA256SUMS
' sh "$backup"
```

El backup contiene una key privada: debe permanecer root-only y fuera del repo.

## Cambio propuesto

Ventana recomendada: 15 minutos de bajo trafico. La recarga NGINX no reinicia
Docker ni Django.

```bash
sudo install -o root -g root -m 644 "$NEW_FULLCHAIN" \
  /etc/apache2/certs/fullchain.crt

# Solo si Infra entrega una key nueva aprobada:
sudo install -o root -g www-data -m 640 "$NEW_KEY" \
  /etc/apache2/certs/secretarianaf.gob.ar.key

sudo nginx -t
sudo systemctl reload nginx
```

No editar NGINX si se conservan los paths actuales. No ejecutar Certbot.

## Verificacion de exito

Sin `-k`:

```bash
openssl s_client -connect 127.0.0.1:443 \
  -servername hml-sisoc.secretarianaf.gob.ar </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -fingerprint -sha256

curl --max-time 8 -fsS --resolve \
  hml-sisoc.secretarianaf.gob.ar:443:127.0.0.1 \
  https://hml-sisoc.secretarianaf.gob.ar/health/

curl --max-time 8 -fsS --resolve \
  hml-sisoc.secretarianaf.gob.ar:443:127.0.0.1 \
  https://hml-sisoc.secretarianaf.gob.ar/mobile/
```

Ademas validar desde un cliente externo autorizado que resuelva el dominio.

## Detectar fallo

- `nginx -t` no finaliza exitosamente;
- certificado y key no coinciden;
- cadena incompleta o issuer inesperado;
- SAN incorrecto;
- `curl` sin `-k` sigue fallando;
- NGINX no queda activo despues de reload;
- backend/mobile dejan de responder.

Ante cualquier fallo previo a reload, no recargar NGINX.

## Rollback

```bash
sudo cp -a "$backup/fullchain.crt" /etc/apache2/certs/fullchain.crt
sudo cp -a "$backup/secretarianaf.gob.ar.key" \
  /etc/apache2/certs/secretarianaf.gob.ar.key
sudo nginx -t
sudo systemctl reload nginx
```

El rollback restaura disponibilidad previa, pero vuelve al certificado vencido.
Preservar evidencia y coordinar material correcto con Infra.
