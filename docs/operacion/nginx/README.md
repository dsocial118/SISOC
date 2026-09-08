# Nginx de SISOC

`sisoc-produccion.conf` es la referencia del vhost de producción.

## La cadena TLS tiene que estar completa

`ssl_certificate` apunta a `fullchain.crt`, que debe contener **el certificado
del sitio y el intermedio**, en ese orden. Si sólo tiene el de hoja, los
navegadores y `curl` igual funcionan —completan la cadena por AIA— pero
**Android no lo hace**: las apps móviles fallan con un `Network Error` genérico
en todas las requests, sin ninguna pista de la causa.

Ya pasó dos veces: al equipo de SISOC - Mobile (comedores) le llevó días
diagnosticarlo, y volvió a aparecer con DataCalle en septiembre de 2026.

**Verificación** (tiene que dar **2**, no 1):

```bash
openssl s_client -connect sisoc.secretarianaf.gob.ar:443 \
  -servername sisoc.secretarianaf.gob.ar </dev/null 2>/dev/null \
  | grep -c "BEGIN CERTIFICATE"
```

Y la validación completa no debe dar error:

```bash
openssl s_client -connect sisoc.secretarianaf.gob.ar:443 \
  -servername sisoc.secretarianaf.gob.ar </dev/null 2>&1 \
  | grep "Verify return code"
# esperado: Verify return code: 0 (ok)
# síntoma:  Verify return code: 21 (unable to verify the first certificate)
```

**Arreglo**: concatenar el intermedio de la CA al certificado del sitio y
recargar nginx.

```bash
cat sitio.crt intermedio.crt > /etc/apache2/certs/fullchain.crt
nginx -t && systemctl reload nginx
```

El intermedio actual es **Sectigo Public Server Authentication CA DV R36**.
Conviene repetir la verificación después de cada renovación del certificado:
es el momento en el que se vuelve a perder.
