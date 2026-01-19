# Diagramas de Flujo - Aceptación al Programa por Rol

## Diagrama 1: Flujo General de Aceptación

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPORTACIÓN DE EXPEDIENTE                     │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Crear Legajo   │
                    │  Asignar Rol    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌──────────┐        ┌──────────────┐
   │BENEFIC. │          │RESPONSAB.│        │BENEFIC. Y    │
   │         │          │          │        │RESPONSAB.    │
   └────┬────┘          └────┬─────┘        └──────┬───────┘
        │                    │                     │
        │                    │                     │
        ▼                    ▼                     ▼
   ┌─────────────┐      ┌──────────────┐    ┌──────────────┐
   │ Validación  │      │ NO se valida │    │ Validación   │
   │ Técnica     │      │ (es solo     │    │ Técnica      │
   │ REQUERIDA   │      │  responsable)│    │ REQUERIDA    │
   └────┬────────┘      └──────┬───────┘    └──────┬───────┘
        │                      │                   │
        ▼                      ▼                   ▼
   ┌─────────────┐      ┌──────────────┐    ┌──────────────┐
   │ APROBADO?   │      │ ACEPTADO AL  │    │ APROBADO?    │
   │             │      │ PROGRAMA     │    │              │
   │ SÍ / NO     │      │ (sin cupo)   │    │ SÍ / NO      │
   └────┬────────┘      └──────────────┘    └──────┬───────┘
        │                                          │
        ├─ NO ──────────────────────────────────┐  │
        │                                       │  │
        │                                       ▼  ▼
        │                                   ┌──────────────┐
        │                                   │ Cruce SINTYS │
        │                                   │ REQUERIDO    │
        │                                   └──────┬───────┘
        │                                          │
        │                                          ▼
        │                                   ┌──────────────┐
        │                                   │ MATCH?       │
        │                                   │              │
        │                                   │ SÍ / NO      │
        │                                   └──────┬───────┘
        │                                          │
        │                    ┌─────────────────────┼─────────────────┐
        │                    │                     │                 │
        │                    ▼                     ▼                 ▼
        │              ┌──────────────┐    ┌──────────────┐   ┌──────────────┐
        │              │ DENTRO CUPO  │    │ FUERA CUPO   │   │ RECHAZADO    │
        │              │ (Aceptado)   │    │ (Lista esp.) │   │ (No entra)   │
        │              └──────────────┘    └──────────────┘   └──────────────┘
        │
        └─ SÍ ──────────────────────────────────────────────────────────────┐
                                                                            │
                                                                            ▼
                                                                    ┌──────────────┐
                                                                    │ RECHAZADO    │
                                                                    │ (No entra)   │
                                                                    └──────────────┘
```

---

## Diagrama 2: Flujo de Responsable Simple

```
┌──────────────────────────────────────────────────────────────┐
│              RESPONSABLE SIMPLE (SOLO RESPONSABLE)            │
└────────────────────────────┬─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Crear Legajo    │
                    │ rol=RESPONSABLE │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ¿Validación?    │
                    │ NO (es solo     │
                    │ responsable)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ¿Cruce SINTYS?  │
                    │ NO (es solo     │
                    │ responsable)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ¿Ocupa Cupo?    │
                    │ NO              │
                    │ estado_cupo=    │
                    │ NO_EVAL         │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ✅ ACEPTADO AL  │
                    │ PROGRAMA        │
                    │ (sin cupo)      │
                    └─────────────────┘
```

---

## Diagrama 3: Flujo de Beneficiario Simple

```
┌──────────────────────────────────────────────────────────────┐
│           BENEFICIARIO SIMPLE (SOLO BENEFICIARIO)             │
└────────────────────────────┬─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Crear Legajo    │
                    │ rol=BENEFICIARIO│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Validación      │
                    │ Técnica         │
                    │ REQUERIDA       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ¿APROBADO?      │
                    └────┬────────┬───┘
                         │        │
                    NO ◄─┘        └─► SÍ
                         │             │
                         ▼             ▼
                    ┌─────────┐   ┌──────────────┐
                    │RECHAZADO│   │ Cruce SINTYS │
                    │(No entra)   │ REQUERIDO    │
                    └─────────┘   └──────┬───────┘
                                         │
                                ┌────────▼────────┐
                                │ ¿MATCH?         │
                                └────┬────────┬───┘
                                     │        │
                                NO ◄─┘        └─► SÍ
                                     │             │
                                     ▼             ▼
                            ┌──────────────┐ ┌──────────────┐
                            │ FUERA CUPO   │ │ DENTRO CUPO  │
                            │ (Lista esp.) │ │ (Aceptado)   │
                            └──────────────┘ └──────────────┘
```

---

## Diagrama 4: Flujo de Beneficiario y Responsable

```
┌──────────────────────────────────────────────────────────────┐
│      BENEFICIARIO Y RESPONSABLE (AMBOS ROLES)                 │
└────────────────────────────┬─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Crear Legajo    │
                    │ rol=BENEFICIARIO│
                    │ _Y_RESPONSABLE  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Validación      │
                    │ Técnica         │
                    │ REQUERIDA       │
                    │ (es beneficiario)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ¿APROBADO?      │
                    └────┬────────┬───┘
                         │        │
                    NO ◄─┘        └─► SÍ
                         │             │
                         ▼             ▼
                    ┌─────────┐   ┌──────────────┐
                    │RECHAZADO│   │ Cruce SINTYS │
                    │(No entra)   │ REQUERIDO    │
                    └─────────┘   │ (es benefic.)
                                  └──────┬───────┘
                                         │
                                ┌────────▼────────┐
                                │ ¿MATCH?         │
                                └────┬────────┬───┘
                                     │        │
                                NO ◄─┘        └─► SÍ
                                     │             │
                                     ▼             ▼
                            ┌──────────────┐ ┌──────────────┐
                            │ FUERA CUPO   │ │ DENTRO CUPO  │
                            │ (Lista esp.) │ │ (Aceptado)   │
                            │ (es benefic.)│ │ (es benefic.)│
                            └──────────────┘ └──────────────┘
                                     │             │
                                     └─────┬───────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Puede ser   │
                                    │ responsable │
                                    │ de hijos    │
                                    └─────────────┘
```

---

## Diagrama 5: Flujo de Responsable → Beneficiario y Responsable

```
┌──────────────────────────────────────────────────────────────┐
│    RESPONSABLE QUE SE CONVIERTE EN BENEFICIARIO Y RESPONSABLE  │
└────────────────────────────┬─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Importación     │
                    │ rol=RESPONSABLE │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Reprocesamiento │
                    │ Detecta:        │
                    │ doc_beneficiario│
                    │ = doc_responsab.│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Actualizar Rol  │
                    │ RESPONSABLE →   │
                    │ BENEFICIARIO_Y_ │
                    │ RESPONSABLE     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Validación      │
                    │ Técnica         │
                    │ REQUERIDA       │
                    │ (es beneficiario)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ ¿APROBADO?      │
                    └────┬────────┬───┘
                         │        │
                    NO ◄─┘        └─► SÍ
                         │             │
                         ▼             ▼
                    ┌─────────┐   ┌──────────────┐
                    │RECHAZADO│   │ Cruce SINTYS │
                    │(No entra)   │ REQUERIDO    │
                    └─────────┘   └──────┬───────┘
                                         │
                                ┌────────▼────────┐
                                │ ¿MATCH?         │
                                └────┬────────┬───┘
                                     │        │
                                NO ◄─┘        └─► SÍ
                                     │             │
                                     ▼             ▼
                            ┌──────────────┐ ┌──────────────┐
                            │ FUERA CUPO   │ │ DENTRO CUPO  │
                            │ (Lista esp.) │ │ (Aceptado)   │
                            └──────────────┘ └──────────────┘
```

---

## Diagrama 6: Flujo de Responsable con Hijos

```
┌──────────────────────────────────────────────────────────────┐
│              RESPONSABLE CON HIJOS A CARGO                     │
└────────────────────────────┬─────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐         ┌─────────┐
   │RESPONSAB│          │HIJO 1   │         │HIJO 2   │
   │         │          │         │         │         │
   └────┬────┘          └────┬────┘         └────┬────┘
        │                    │                   │
        ▼                    ▼                   ▼
   ┌─────────────┐      ┌──────────────┐   ┌──────────────┐
   │ NO se       │      │ Validación   │   │ Validación   │
   │ valida      │      │ Técnica      │   │ Técnica      │
   │ (es solo    │      │ REQUERIDA    │   │ REQUERIDA    │
   │ responsable)│      └──────┬───────┘   └──────┬───────┘
   └────┬────────┘             │                  │
        │                      ▼                  ▼
        │                 ┌──────────────┐   ┌──────────────┐
        │                 │ APROBADO?    │   │ APROBADO?    │
        │                 └──┬────────┬──┘   └──┬────────┬──┘
        │                    │        │         │        │
        │              NO ◄──┘        └──► SÍ  │        │
        │                    │             │    │        │
        │                    ▼             ▼    ▼        ▼
        │              ┌──────────┐  ┌──────────────┐
        │              │RECHAZADO │  │ Cruce SINTYS │
        │              │(No entra)│  │ REQUERIDO    │
        │              └──────────┘  └──────┬───────┘
        │                                    │
        │                           ┌────────▼────────┐
        │                           │ ¿MATCH?         │
        │                           └────┬────────┬───┘
        │                                │        │
        │                           NO ◄─┘        └─► SÍ
        │                                │             │
        │                                ▼             ▼
        │                         ┌──────────────┐ ┌──────────────┐
        │                         │ FUERA CUPO   │ │ DENTRO CUPO  │
        │                         │ (Lista esp.) │ │ (Aceptado)   │
        │                         └──────────────┘ └──────────────┘
        │
        ▼
   ┌─────────────────────────────────────────────────────┐
   │ RESULTADO FINAL:                                    │
   │ - Responsable: NO_EVAL (0 cupo)                     │
   │ - Hijo 1: DENTRO (1 cupo) si APROBADO+MATCH        │
   │ - Hijo 2: DENTRO (1 cupo) si APROBADO+MATCH        │
   │ - Total: 2 cupos (solo los hijos)                  │
   └─────────────────────────────────────────────────────┘
```

---

## Diagrama 7: Matriz de Decisión - Cupo

```
                    ┌─────────────────────────────────────┐
                    │ ¿PUEDE OCUPAR CUPO?                 │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │ ¿Rol es RESPONSABLE?            │
                    └────┬──────────────────────┬──────┘
                         │                      │
                    SÍ ◄─┘                      └─► NO
                         │                         │
                         ▼                         ▼
                    ┌──────────────┐         ┌──────────────┐
                    │ NO OCUPA     │         │ ¿APROBADO?   │
                    │ CUPO         │         └────┬─────┬───┘
                    │ (NO_EVAL)    │              │     │
                    └──────────────┘         NO ◄─┘     └─► SÍ
                                                 │         │
                                                 ▼         ▼
                                            ┌────────┐ ┌──────────────┐
                                            │NO_EVAL │ │ ¿MATCH?      │
                                            └────────┘ └────┬─────┬───┘
                                                           │     │
                                                      NO ◄─┘     └─► SÍ
                                                           │         │
                                                           ▼         ▼
                                                      ┌────────┐ ┌──────────────┐
                                                      │ FUERA  │ │ ¿YA OCUPA    │
                                                      │ (lista)│ │ CUPO EN PROV?│
                                                      └────────┘ └────┬─────┬───┘
                                                                      │     │
                                                                 SÍ ◄─┘     └─► NO
                                                                      │         │
                                                                      ▼         ▼
                                                                 ┌────────┐ ┌──────────────┐
                                                                 │ FUERA  │ │ ¿CUPO DISP?  │
                                                                 │ (lista)│ └────┬─────┬───┘
                                                                 └────────┘      │     │
                                                                            NO ◄─┘     └─► SÍ
                                                                                 │         │
                                                                                 ▼         ▼
                                                                            ┌────────┐ ┌──────────────┐
                                                                            │ FUERA  │ │ DENTRO       │
                                                                            │ (lista)│ │ (Aceptado)   │
                                                                            └────────┘ └──────────────┘
```

---

## Leyenda

- ✅ = Aceptado
- ❌ = Rechazado
- ⏳ = En lista de espera
- → = Flujo
- ◄─ = Decisión
- ▼ = Siguiente paso
