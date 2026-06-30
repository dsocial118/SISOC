# Exportacion de comedores con permiso de listado y exportacion

## Contexto

La opcion "Exportar" del listado de comedores debe estar disponible solo para
usuarios que puedan ver el listado y que, ademas, tengan el permiso explicito de
exportacion CSV.

El acceso al listado de comedores se habilita con alguno de estos permisos
funcionales de visualizacion:

- `comedores.view_comedor`
- `admisiones.view_admision`
- `acompanamientos.view_informacionrelevante`

La capacidad de exportar se controla con:

- `auth.role_exportar_a_csv`

Antes del ajuste, la UI y el endpoint no expresaban de forma clara esa doble
condicion para el flujo de comedores.

## Cambio

La exportacion de comedores exige dos condiciones:

- acceso al listado de comedores mediante alguno de los permisos funcionales de
  visualizacion;
- permiso explicito de exportacion `auth.role_exportar_a_csv`.

Los roles administradores/globales (`auth.role_admin`, `auth.role_administrador`,
`auth.role_superadmin`) y superusuarios quedan exceptuados de esa doble
condicion. El CSV se construye con `ComedorService.get_filtered_comedores`, por
lo que conserva el mismo alcance de datos que ya aplica el listado para el
usuario.

El componente compartido `search_bar.html` ahora puede recibir:

- permisos canonicos que habilitan el listado;
- un permiso requerido adicional para exportar;
- permisos administradores/globales que exceptuan la doble condicion.

Esto evita depender de aliases legacy de grupos para mostrar el boton de
exportacion.

## Validacion

Se agregaron tests de regresion para:

- rechazar exportacion cuando falta el permiso de listado o falta el permiso
  explicito de exportacion;
- permitir exportacion con ambos permisos;
- permitir exportacion a roles administradores/globales;
- mostrar el boton de exportacion en la lista solo cuando el usuario tiene ambos
  permisos o rol administrador/global.
