# 2026-09-24 - Homogeneizar los buscadores: filtros combinables en todos los listados

## Contexto
- Los 18 listados principales tenian buscadores con modos distintos. Auditados
  renderizando cada pantalla:
  - **11 con filtros combinables** (comedores, admisiones tecnicos y legales,
    acompanamientos, rendicion, dispositivos, centros CDF, beneficiarios,
    responsables, VAT centros, celiaquia).
  - **2 con busqueda AJAX por texto** (importar expedientes, organizaciones).
  - **5 con busqueda simple por texto** (centro de infancia, VPSL itinerarios,
    VPSL sedes, VAT modalidades de cursado, VAT planes curriculares).
- Ademas, en los dos catalogos de VAT el buscador era **decorativo**: el
  componente se renderizaba pero la vista nunca aplicaba `busqueda`.

## Cambios aplicados
Se migraron **6 listados** al componente de filtros combinables, conservando en
cada uno lo que ya buscaba:

| Listado | Antes | Config nueva |
|---|---|---|
| Importar expedientes | AJAX texto | `importarexpediente/filter_config.py` |
| Centro de Desarrollo Infantil | texto simple | `centrodeinfancia/filter_config.py` |
| VPSL itinerarios | texto simple + panel propio | `ver_para_ser_libre/filter_config.py` |
| VPSL sedes | texto simple | `ver_para_ser_libre/filter_config.py` |
| VAT modalidades de cursado | texto simple (inerte) | `VAT/catalogo_filter_config.py` |
| VAT planes curriculares | texto simple (inerte) | `VAT/catalogo_filter_config.py` |

Cada `filter_config` define `FIELD_MAP` / `FIELD_TYPES` / operadores /
`FILTER_FIELDS` y su `AdvancedFilterEngine`, igual que comedores y dispositivos.
Las vistas aplican el engine al queryset **antes** de su busqueda propia, que se
mantiene intacta, y exponen `filters_mode`, `filters_config` y `filters_action`.

Detalles por pantalla:
- **VAT modalidades**: ademas de los filtros combinables, ahora la vista aplica
  `busqueda` por nombre; antes se ignoraba.
- **VAT planes**: conserva sus filtros propios de `titulo` y `activo`.
- **Importar expedientes**: la vista AJAX (`importarexpedientes_ajax`) tambien
  honra `filters`, para que el endpoint siga sirviendo igual que el listado.
- **VPSL itinerarios**: el modulo tenia un panel de filtros propio y un
  comentario en el template explicando por que no se habia migrado (la busqueda
  "todos" hace un OR entre siete campos, `estado` mapea texto con una funcion,
  `localidad` cruza tres rutas y `provincia` depende de permisos: nada de eso es
  expresable con el engine, que combina un `Q` por fila con AND). Se respeto esa
  decision: el panel y su texto libre **siguen existiendo**, re-apuntados con
  `form="filters-form"` para viajar en el mismo submit que los filtros
  combinables. Los combinables se suman, no reemplazan.

## Decisiones y limites
- **Organizaciones quedo fuera a proposito**: ya se migro a filtros combinables
  en la rama del issue #2505 (`organizaciones/filter_config.py`). Incluirlo aca
  generaria un conflicto con ese trabajo.
- Solo se homogeneizo el **modo de busqueda**. Siguen difiriendo:
  - "Exportar busqueda": 11 listados no lo tienen.
  - "Agregar": depende de si la entidad tiene alta (admisiones, acompanamientos
    y rendicion no la tienen como flujo propio).

## Impacto esperado
- 17 de los 18 listados usan el mismo buscador de filtros combinables, con la
  misma UI y el mismo motor.
- Ninguna busqueda existente cambia de semantica: el parametro `busqueda` sigue
  funcionando en todos los listados que lo tenian, y los filtros propios de
  planes curriculares e itinerarios se conservan.
- Los dos catalogos de VAT pasan a buscar de verdad.

## Validación
- `pytest -n auto`: 5505 passed, 14 skipped. Test nuevo
  `tests/test_buscadores_homogeneos.py` (20 casos): verifica que cada listado
  migrado exponga la UI y la config, que los campos declaren tipo y operadores
  validos, que los filtros efectivamente filtren (incluida una combinacion de
  dos campos) y que la busqueda previa de cada pantalla siga andando.
- `tests/test_csv_export_architecture.py` sigue fallando, pero ya fallaba antes
  (rompe al decodificar un archivo `cp1252` de `xlwt`).
- `black` y `djlint` sobre lo tocado.

## Riesgos y rollback
- Riesgo principal: no se probo en el navegador. Conviene revisar visualmente
  VPSL itinerarios, que es la unica pantalla donde conviven el panel propio y la
  barra de filtros combinables.
- Rollback: revertir el commit. No hay migraciones.
