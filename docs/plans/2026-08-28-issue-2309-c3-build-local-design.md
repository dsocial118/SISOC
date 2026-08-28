# #2309 — C3: CI y despliegue por build local desde SHA

## Decisión aprobada

C3 no publicará imágenes de Dispositivos en un registry ni promoverá un digest
OCI entre entornos. Cada runner autorizado construirá localmente el runtime
desde el mismo SHA de Git aprobado. El rollback será reconstruir desde el SHA
anterior, no recuperar una imagen publicada.

Se acepta que dos builds hechos en momentos o entornos distintos no son
necesariamente idénticos a nivel binario. El Dockerfile aún consume la etiqueta
de base `python:3.11.15-slim-bookworm`, paquetes APT y el modelo OCR remoto;
Python sí usa versiones fijadas. C3 debe hacer visible esa diferencia, no
ocultarla como si fuera una promoción por digest.

## Alternativas evaluadas

| Alternativa | Resultado | Motivo |
| --- | --- | --- |
| Registry privado con digest | Misma imagen entre ambientes | Descartado: agrega publicación y operación de registry. |
| Archivo OCI como release o artifact | Imagen transferible sin registry | Descartado: mantiene publicación de imagen y complejidad de retención/importación. |
| Build local desde SHA | Sin publicación de imagen | Elegido: reutiliza el modelo de runners existente, con trazabilidad de inputs y rollback por SHA. |

## Contrato de C3

1. Los filtros de paths ejecutan el pipeline de Dispositivos para cambios en el
   vertical, su runtime, Dockerfile, dependencias, contratos o workflows; los
   checks transversales no se omiten.
2. Antes de construir o arrancar, el runner verifica que `origin/<branch>` sea
   el SHA exacto autorizado. Un SHA obsoleto se omite sin tocar servicios.
3. Cada build deja un manifiesto con SHA fuente, checksum de Dockerfile y
   requirements, imagen base resuelta, inputs externos observados, image ID
   local, fecha, runner y resultado de las verificaciones.
4. QA, HML y PRD sólo pueden construir el mismo SHA fuente. Sus manifiestos se
   comparan; una diferencia se registra y bloquea promoción posterior hasta
   evaluación humana. No se afirma igualdad de digest.
5. El deploy/restart/rollback del vertical no inicia ni detiene el stack Django
   global. El rollback usa el SHA previo documentado y vuelve a construirlo.

## Límites y dependencias

- C3 no modifica aún runners, Environments, secretos, servidores ni datos.
- El formato y retención del manifiesto, el destino independiente y el permiso
  operativo de los runners se deben confirmar antes de implementar despliegue.
- C4 continúa siendo dueño de routing público, identidad, health,
  observabilidad y validación de rollback en QA/HML.
- Si se requiere reproducibilidad binaria o promoción exacta, esta decisión se
  revisa y se adopta un artefacto OCI inmutable.

## Criterios de aceptación ajustados

- Un cambio acotado dispara el pipeline de Dispositivos y deja un manifiesto de
  build trazable; un cambio ajeno no lo despliega.
- El mismo SHA fuente se verifica y reconstruye de forma independiente por
  ambiente, sin reiniciar el monolito.
- Se puede volver al SHA anterior sin publicar ni descargar una imagen propia.
- La comparación de manifiestos evidencia cualquier deriva; no equivale a un
  digest promovido.
