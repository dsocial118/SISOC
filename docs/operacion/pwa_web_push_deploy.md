# Deploy de Web Push PWA

## Objetivo

Dejar operativas las notificaciones nativas de la PWA para mensajes de
rendicion en QA y Produccion.

## Alcance

- Backend Django que genera y envia web push.
- PWA que registra service worker y suscripciones del navegador.
- Variables VAPID por ambiente.

## Requisitos previos

- Dominio publicado bajo HTTPS.
- Deploy del backend con la dependencia `pywebpush`.
- Deploy del frontend/mobile con el service worker nuevo.
- Acceso para configurar variables de entorno del ambiente.

## Variables de entorno obligatorias

Definir en cada ambiente:

- `PWA_WEB_PUSH_PUBLIC_KEY`
- `PWA_WEB_PUSH_PRIVATE_KEY`
- `PWA_WEB_PUSH_SUBJECT`

Reglas:

- usar un par VAPID distinto por ambiente;
- `PWA_WEB_PUSH_SUBJECT` debe ser un mail operativo real, por ejemplo
  `mailto:soporte@sisoc....`;
- no reutilizar las claves locales de desarrollo en QA o Produccion.

## Generacion de claves VAPID

Ejemplo dentro del contenedor/app con `py_vapid` instalado:

```bash
docker compose exec django python -c "from py_vapid import Vapid01, b64urlencode; vapid=Vapid01(); vapid.generate_keys(); private_value=vapid.private_key.private_numbers().private_value.to_bytes(32, 'big'); public_numbers=vapid.public_key.public_numbers(); public_bytes=b'\x04'+public_numbers.x.to_bytes(32,'big')+public_numbers.y.to_bytes(32,'big'); print(b64urlencode(public_bytes)); print(b64urlencode(private_value))"
```

Salida:

- primera linea: `PWA_WEB_PUSH_PUBLIC_KEY`
- segunda linea: `PWA_WEB_PUSH_PRIVATE_KEY`

## Checklist de deploy

1. Actualizar variables de entorno del ambiente con las tres variables VAPID.
2. Desplegar backend con la nueva imagen para instalar `pywebpush`.
3. Ejecutar migraciones, incluyendo `pwa.0013_pushsubscriptionpwa`.
4. Desplegar la build nueva de la PWA/mobile.
5. Reiniciar/recrear el servicio Django para que lea las variables nuevas.
6. Verificar que el ambiente responda con `PWA_WEB_PUSH_ENABLED=True`.

## Comandos de referencia

Adaptar a la operacion real del ambiente.

```bash
docker compose build django
docker compose up -d django
docker compose exec django python manage.py migrate
docker compose exec django python manage.py shell -c "from django.conf import settings; print(settings.PWA_WEB_PUSH_ENABLED)"
```

## Validacion funcional post deploy

1. Abrir la PWA desde el dominio final del ambiente.
2. Ingresar con un usuario PWA con permiso de rendicion.
3. Aceptar el permiso de notificaciones del navegador/sistema.
4. Generar desde Web una revision de documento de rendicion del scope del usuario.
5. Confirmar:
   - aparece la push nativa del dispositivo;
   - al tocarla abre la PWA;
   - navega al detalle de la rendicion correspondiente;
   - la campanita interna sigue mostrando el mensaje.

## Troubleshooting rapido

- Si la campanita funciona pero no llega push:
  - revisar que `PWA_WEB_PUSH_ENABLED` sea `True`;
  - revisar que el navegador haya otorgado permiso;
  - revisar que exista una fila en `PushSubscriptionPWA`;
  - revisar que el backend tenga `pywebpush` instalado;
  - revisar que el ambiente sea HTTPS y origen final, no localhost externo.

- Si la push llega pero no abre la rendicion:
  - revisar que el service worker desplegado sea el nuevo;
  - limpiar/reinstalar la PWA para refrescar el worker;
  - verificar que la URL de destino exista en la version desplegada.

## Notas operativas

- Las suscripciones son por usuario/dispositivo/navegador. Un mismo usuario puede
  tener varias activas.
- Si el proveedor push devuelve `404` o `410`, SISOC desactiva automaticamente
  esa suscripcion.
