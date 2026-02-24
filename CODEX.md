# CODEX.md

Instrucciones específicas para Codex en este repo.

Fuente de verdad: `AGENTS.md`.

## Orden de lectura recomendado

1. `AGENTS.md`
2. `docs/ia/STYLE_GUIDE.md`
3. `docs/ia/ARCHITECTURE.md`
4. `docs/ia/TESTING.md`
5. Archivos concretos del módulo a modificar

## Forma de trabajo esperada (Codex)

## 1) Explorar contexto rápido sin romper alcance

- Buscar implementaciones similares antes de editar.
- Revisar tests existentes del módulo para copiar patrón.
- Confirmar permisos, serializers, forms y services reales.
- Evitar suposiciones sobre modelos/campos sin verificar.

## 2) Decidir diff mínimo

Antes de editar, definir:
- cuál es el comportamiento a cambiar,
- cuál es el archivo responsable,
- cuál es el test mínimo que lo cubre.

Si el cambio requiere tocar muchos archivos, explicar por qué.

## 3) Reportar cambios de forma útil

Al entregar, incluir:
- archivos tocados,
- comportamiento nuevo/corregido,
- validación ejecutada,
- supuestos,
- riesgos,
- mejoras cercanas detectadas (opcional).

## 4) Tareas grandes: trabajar por fases

Para refactors/features grandes:
- dividir en fases incrementales,
- mantener el sistema funcional entre fases,
- separar cambios estructurales de cambios funcionales cuando sea posible,
- proponer el plan antes de expandir alcance.

## 5) Mejoras cercanas sin scope creep

Codex puede detectar mejoras cercanas, pero:
- no las implementa fuera de alcance sin aprobación,
- las reporta separadas,
- indica impacto y costo estimado.

Formato sugerido:

```md
## Mejoras cercanas detectadas (opcional)
- [Impacto alto | costo bajo] ...
```

## Heurísticas útiles para este repo

- Lógica de negocio suele vivir en `services/`.
- Views Django y DRF coexisten; validar patrón por app.
- Tests usan `pytest`, fixtures y `monkeypatch` con frecuencia.
- Templates usan `djlint`; evitar meter lógica compleja en HTML.
- Logging y errores tienen patrones ya implementados en `config/settings.py` y `core/utils.py`.

## Checklist de cierre (Codex)

- Leí `AGENTS.md` y guías relevantes de `docs/ia/`.
- No inventé APIs/campos/modelos.
- Mantuve diff chico y enfocado.
- No toqué configs de tooling/CI sin pedido.
- Agregué tests mínimos o expliqué por qué no.
- Declaré supuestos y riesgos.
- Reporté mejoras cercanas solo como propuesta.

## Ejemplo de pedido (Codex)

```md
Corregí el manejo de errores en `core/services/image_service.py` cuando la ruta es inválida.
Fix mínimo + test de regresión.
No refactorices el módulo completo.
Podés proponer mejoras cercanas sin implementarlas.
```
