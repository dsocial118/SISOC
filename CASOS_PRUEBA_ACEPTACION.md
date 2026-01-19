# Casos de Prueba - Aceptación al Programa por Rol

## Caso 1: Solo Beneficiario - Aceptado
**Descripción**: Persona que solo recibe prestaciones

**Datos de Entrada**:
- Nombre: Juan García
- DNI: 20000000001
- Rol: BENEFICIARIO
- Validación Técnica: APROBADO
- Cruce SINTYS: MATCH

**Validaciones Esperadas**:
- ✅ Se crea legajo con rol=BENEFICIARIO
- ✅ Se valida técnicamente (APROBADO)
- ✅ Se incluye en cruce SINTYS
- ✅ Se reserva cupo: estado_cupo=DENTRO, es_titular_activo=True
- ✅ Ocupa 1 cupo en la provincia

**Resultado**: ✅ ACEPTADO AL PROGRAMA

---

## Caso 2: Solo Beneficiario - Rechazado por Técnico
**Descripción**: Persona que solo recibe prestaciones pero es rechazada

**Datos de Entrada**:
- Nombre: María López
- DNI: 20000000002
- Rol: BENEFICIARIO
- Validación Técnica: RECHAZADO
- Cruce SINTYS: (no aplica)

**Validaciones Esperadas**:
- ✅ Se crea legajo con rol=BENEFICIARIO
- ✅ Se rechaza técnicamente (RECHAZADO)
- ✅ NO se incluye en cruce SINTYS
- ✅ NO ocupa cupo: estado_cupo=NO_EVAL, es_titular_activo=False

**Resultado**: ❌ RECHAZADO (no entra al programa)

---

## Caso 3: Solo Beneficiario - No Matchea en SINTYS
**Descripción**: Persona que solo recibe prestaciones pero no está en SINTYS

**Datos de Entrada**:
- Nombre: Carlos Rodríguez
- DNI: 20000000003
- Rol: BENEFICIARIO
- Validación Técnica: APROBADO
- Cruce SINTYS: NO_MATCH

**Validaciones Esperadas**:
- ✅ Se crea legajo con rol=BENEFICIARIO
- ✅ Se valida técnicamente (APROBADO)
- ✅ Se incluye en cruce SINTYS
- ❌ NO matchea (NO_MATCH)
- ✅ NO ocupa cupo: estado_cupo=FUERA, es_titular_activo=False (lista de espera)

**Resultado**: ⏳ EN LISTA DE ESPERA (no entra al programa aún)

---

## Caso 4: Solo Responsable - Aceptado
**Descripción**: Persona que solo es responsable legal

**Datos de Entrada**:
- Nombre: Pedro Martínez
- DNI: 20000000004
- Rol: RESPONSABLE
- Validación Técnica: (no aplica)
- Cruce SINTYS: (no aplica)

**Validaciones Esperadas**:
- ✅ Se crea legajo con rol=RESPONSABLE
- ✅ NO se valida técnicamente (es responsable)
- ✅ NO se incluye en cruce SINTYS
- ✅ NO ocupa cupo: estado_cupo=NO_EVAL, es_titular_activo=False
- ✅ Puede ser responsable de hijos en el expediente

**Resultado**: ✅ ACEPTADO AL PROGRAMA (como responsable, sin cupo)

---

## Caso 5: Beneficiario y Responsable - Aceptado
**Descripción**: Persona que es responsable Y recibe prestaciones

**Datos de Entrada**:
- Nombre: Ana Fernández
- DNI: 20000000005
- Rol: BENEFICIARIO_Y_RESPONSABLE
- Validación Técnica: APROBADO
- Cruce SINTYS: MATCH

**Validaciones Esperadas**:
- ✅ Se crea legajo con rol=BENEFICIARIO_Y_RESPONSABLE
- ✅ Se valida técnicamente (APROBADO) - porque es beneficiario
- ✅ Se incluye en cruce SINTYS - porque es beneficiario
- ✅ Se reserva cupo: estado_cupo=DENTRO, es_titular_activo=True
- ✅ Ocupa 1 cupo en la provincia
- ✅ Puede ser responsable de hijos en el expediente

**Resultado**: ✅ ACEPTADO AL PROGRAMA (como beneficiario y responsable)

---

## Caso 6: Responsable que se Convierte en Beneficiario y Responsable
**Descripción**: Persona importada como responsable, luego se detecta que es beneficiario_y_responsable

**Datos de Entrada - Importación Inicial**:
- Nombre: Laura Sánchez
- DNI: 20000000006
- Rol: RESPONSABLE (inicialmente)
- Datos de responsable: Sí (es responsable de sus hijos)

**Datos de Entrada - Reprocesamiento**:
- Mismo ciudadano
- Documento del responsable = Documento del beneficiario (mismo)
- Sistema detecta: es beneficiario_y_responsable

**Validaciones Esperadas**:
1. **Importación inicial**:
   - ✅ Se crea legajo con rol=RESPONSABLE
   - ✅ estado_cupo=NO_EVAL

2. **Reprocesamiento**:
   - ✅ Se detecta que es beneficiario_y_responsable
   - ✅ Se actualiza rol: RESPONSABLE → BENEFICIARIO_Y_RESPONSABLE
   - ✅ Se valida técnicamente (APROBADO)
   - ✅ Se incluye en cruce SINTYS
   - ✅ Se reserva cupo: estado_cupo=DENTRO, es_titular_activo=True

**Resultado**: ✅ ACEPTADO AL PROGRAMA (como beneficiario y responsable)

---

## Caso 7: Responsable con Hijos
**Descripción**: Responsable que tiene hijos a cargo en el mismo expediente

**Datos de Entrada**:
- **Responsable**: Pedro García
  - DNI: 20000000007
  - Rol: RESPONSABLE
  - Validación: (no aplica)
  - Cupo: NO

- **Hijo 1**: Juan García
  - DNI: 20000000008
  - Rol: BENEFICIARIO
  - Validación: APROBADO
  - Cruce: MATCH
  - Cupo: SÍ (1 cupo)

- **Hijo 2**: María García
  - DNI: 20000000009
  - Rol: BENEFICIARIO
  - Validación: APROBADO
  - Cruce: MATCH
  - Cupo: SÍ (1 cupo)

**Validaciones Esperadas**:
- ✅ Responsable: estado_cupo=NO_EVAL, es_titular_activo=False
- ✅ Hijo 1: estado_cupo=DENTRO, es_titular_activo=True
- ✅ Hijo 2: estado_cupo=DENTRO, es_titular_activo=True
- ✅ Total cupo usado: 2 (solo los hijos)
- ✅ Relaciones familiares creadas correctamente

**Resultado**: ✅ ACEPTADOS AL PROGRAMA (responsable + 2 hijos)

---

## Caso 8: Responsable con Hijo Rechazado
**Descripción**: Responsable que tiene un hijo rechazado

**Datos de Entrada**:
- **Responsable**: Carlos López
  - DNI: 20000000010
  - Rol: RESPONSABLE
  - Cupo: NO

- **Hijo**: Ana López
  - DNI: 20000000011
  - Rol: BENEFICIARIO
  - Validación: RECHAZADO
  - Cupo: NO

**Validaciones Esperadas**:
- ✅ Responsable: estado_cupo=NO_EVAL, es_titular_activo=False
- ✅ Hijo: estado_cupo=NO_EVAL, es_titular_activo=False
- ✅ Total cupo usado: 0
- ✅ Relaciones familiares creadas

**Resultado**: ✅ ACEPTADOS AL PROGRAMA (responsable + hijo rechazado)

---

## Caso 9: Ciudadano Dual - Responsable en Expediente 1, Beneficiario en Expediente 2
**Descripción**: Mismo ciudadano aparece como responsable en un expediente y beneficiario en otro

**Datos de Entrada**:
- **Expediente 1**:
  - Ciudadano: Roberto Díaz (DNI: 20000000012)
  - Rol: RESPONSABLE
  - Cupo: NO

- **Expediente 2**:
  - Ciudadano: Roberto Díaz (DNI: 20000000012)
  - Rol: BENEFICIARIO
  - Validación: APROBADO
  - Cruce: MATCH
  - Cupo: SÍ

**Validaciones Esperadas**:
- ✅ Expediente 1: estado_cupo=NO_EVAL, es_titular_activo=False
- ✅ Expediente 2: estado_cupo=DENTRO, es_titular_activo=True
- ✅ Total cupo usado: 1 (solo en Expediente 2)
- ✅ Cada expediente se valida independientemente

**Resultado**: ✅ ACEPTADO EN AMBOS (con diferentes roles)

---

## Caso 10: Responsable que Ya Ocupa Cupo en Otra Provincia
**Descripción**: Responsable que ya ocupa cupo en otra provincia (no aplica porque responsables no ocupan cupo)

**Datos de Entrada**:
- **Provincia A**:
  - Ciudadano: Sofía Ruiz (DNI: 20000000013)
  - Rol: BENEFICIARIO
  - Estado: DENTRO, es_titular_activo=True

- **Provincia B**:
  - Ciudadano: Sofía Ruiz (DNI: 20000000013)
  - Rol: RESPONSABLE
  - Validación: (no aplica)

**Validaciones Esperadas**:
- ✅ Provincia A: estado_cupo=DENTRO, es_titular_activo=True (1 cupo)
- ✅ Provincia B: estado_cupo=NO_EVAL, es_titular_activo=False (0 cupo)
- ✅ Total cupo usado: 1 (solo en Provincia A)

**Resultado**: ✅ ACEPTADO EN AMBAS (con diferentes roles)

---

## Caso 11: Beneficiario que Ya Ocupa Cupo en Otra Provincia
**Descripción**: Beneficiario que ya ocupa cupo en otra provincia

**Datos de Entrada**:
- **Provincia A**:
  - Ciudadano: Tomás Gómez (DNI: 20000000014)
  - Rol: BENEFICIARIO
  - Estado: DENTRO, es_titular_activo=True

- **Provincia B**:
  - Ciudadano: Tomás Gómez (DNI: 20000000014)
  - Rol: BENEFICIARIO
  - Validación: APROBADO
  - Cruce: MATCH

**Validaciones Esperadas**:
- ✅ Provincia A: estado_cupo=DENTRO, es_titular_activo=True (1 cupo)
- ✅ Provincia B: estado_cupo=FUERA, es_titular_activo=False (lista de espera)
- ✅ Total cupo usado: 1 (solo en Provincia A)
- ✅ Validación: Ya ocupa cupo en otra provincia → FUERA

**Resultado**: ⏳ EN LISTA DE ESPERA EN PROVINCIA B

---

## Matriz de Validación Rápida

| Caso | Rol | Validación | Cruce | Cupo | Resultado |
|------|-----|-----------|-------|------|-----------|
| 1 | BENEFICIARIO | APROBADO | MATCH | DENTRO | ✅ Aceptado |
| 2 | BENEFICIARIO | RECHAZADO | - | NO_EVAL | ❌ Rechazado |
| 3 | BENEFICIARIO | APROBADO | NO_MATCH | FUERA | ⏳ Lista espera |
| 4 | RESPONSABLE | - | - | NO_EVAL | ✅ Aceptado |
| 5 | BENEFICIARIO_Y_RESPONSABLE | APROBADO | MATCH | DENTRO | ✅ Aceptado |
| 6 | RESPONSABLE→BENEFICIARIO_Y_RESPONSABLE | APROBADO | MATCH | DENTRO | ✅ Aceptado |
| 7 | RESPONSABLE + 2 BENEFICIARIOS | APROBADO | MATCH | 2 DENTRO | ✅ Aceptados |
| 8 | RESPONSABLE + BENEFICIARIO RECHAZADO | RECHAZADO | - | NO_EVAL | ✅ Aceptados |
| 9 | RESPONSABLE (Exp1) + BENEFICIARIO (Exp2) | APROBADO | MATCH | 1 DENTRO | ✅ Aceptados |
| 10 | RESPONSABLE (Prov B) | - | - | NO_EVAL | ✅ Aceptado |
| 11 | BENEFICIARIO (Prov B, ya en Prov A) | APROBADO | MATCH | FUERA | ⏳ Lista espera |

---

## Notas Importantes

1. **Responsables puros NUNCA ocupan cupo**, incluso si están APROBADOS + MATCH
2. **Beneficiarios y Responsables ocupan cupo COMO BENEFICIARIOS**, no como responsables
3. **Cada expediente se valida independientemente**, pero se respeta el cupo por provincia
4. **Un ciudadano puede tener diferentes roles en diferentes expedientes**
5. **La validación técnica solo aplica a beneficiarios**, no a responsables puros
6. **El cruce SINTYS solo aplica a beneficiarios**, no a responsables puros
