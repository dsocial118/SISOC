# PAS: circuito mensual de cruces

## Alcance

Se implementó el circuito administrativo mensual de `/pas/cruces` con estado
persistido para la exportación e importación SINTyS.

## Decisiones

- El circuito se identifica por el primer día del mes y registra fecha, usuario
  y archivo de cada transferencia SINTyS.
- La nómina se genera desde `PasPersona`, usando el contrato XLSX ya empleado
  por Celiaquía: `numero_cuil`, `nombre` y `apellido`.
- PAS no posee el dato sexo. No se inventa ni se completa una columna sin
  fuente confirmada.
- El retorno admite XLSX, XLS o CSV hasta 10 MB. La carga no procesa alertas
  todavía: solo registra el archivo y completa la etapa administrativa.
- Justicia, Migraciones, AFIP, BNA y patrimonio permanecen como pendientes.
  RENAPER cuenta con un control diario de supervivencia documentado por
  separado.
- Exportar e importar requiere `pas.change_paspersona`, además de autenticación.

## Riesgos y trabajo pendiente

- Confirmar con SINTyS si PAS debe enviar campos adicionales al contrato mínimo.
- Definir schemas, reintentos, auditoría técnica y reglas de incompatibilidad
  antes de activar los cruces externos.
- Incorporar procesamiento del retorno y una bandeja de alertas cuando el
  formato oficial esté disponible.
