# Alta de Referente Provincial SIMEPI - Fase 3

Se incorpora una pantalla dedicada para que el Equipo Nacional de SIMEPI o un
superusuario genere usuarios con rol fijo `SIMEPI - EGP`. La provincia es
obligatoria y el alta crea un único alcance territorial de provincia completa.

La autorización se valida en la vista mediante el alcance efectivo de
delegación; la sección `SIMEPI` del sidebar es únicamente una ayuda de
navegación. El callback transaccional marca primero el perfil como usuario
provincial y luego sincroniza el alcance, preservando la integridad del alta si
la vinculación territorial falla.
