# 2026-03-31 - Pylint se resuelve con código antes que con supresiones

## Estado

- aceptada

## Contexto

El repositorio ya define `pylint` como herramienta real de linting, pero las
guías para agentes podían dejar margen para resolver avisos con atajos
(`ignore`, `disable` o supresiones amplias) en vez de corregir el código.

## Decisión

- Tratar `.pylintrc` como contrato operativo.
- Resolver avisos de `pylint` con cambios de código primero:
  - simplificar funciones,
  - extraer helpers,
  - mover lógica al boundary correcto,
  - ajustar nombres y estructura,
  - hacer más explícito el flujo.
- Usar `disable` o ignorados solo como último recurso, con el scope mínimo
  posible y justificación documental cuando sea inevitable.

## Consecuencias

- Mejora la calidad estructural del código y reduce deuda técnica oculta.
- Puede aumentar levemente el tiempo de resolución de algunos hallazgos de
  lint, porque evita el atajo de silenciarlos.
- Mantiene alineadas las guías de agentes con la configuración real del repo.
