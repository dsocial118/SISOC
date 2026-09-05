# Requisito: alta de persona sin DNI desde nómina

**Fecha:** 2026-08-03

## Objetivo

Permitir que una persona sin DNI pueda crearse directamente desde la carga a nómina, sin exigir validación previa. En cambio, cuando el alta proviene del módulo de Historia Social Digital, debe mantenerse la validación actual del flujo.

## Comportamiento esperado

### 1) Desde la nómina
- Se debe poder crear un ciudadano con tipo de registro "Sin DNI".
- No debe requerirse validación previa para permitir el alta.
- Una vez creado, debe quedar asociado a la nómina correspondiente.

### 2) Desde Historia Social Digital
- Debe mantenerse el comportamiento vigente de validación.
- Si la persona se carga sin DNI, debe seguir aplicándose la regla de validación correspondiente del flujo actual.

## Regla de negocio

La lógica debe depender del origen del alta:
- si el origen es la nómina, el alta sin DNI debe permitirse sin validación;
- si el origen es Historia Social, debe respetarse la validación vigente.

## Sugerencia de implementación

- Incorporar un parámetro de origen en el flujo de creación de ciudadano, por ejemplo: `origen='nomina'` o `origen='historia_social'`.
- Centralizar la decisión en el servicio que crea el ciudadano y lo agrega a la nómina.
- Evitar duplicar reglas en las vistas y mantener un único punto de decisión.

## Criterios de aceptación

- Se puede crear una persona sin DNI desde la nómina sin bloqueo por validación.
- El mismo caso, al venir desde Historia Social, conserva la validación actual.
- El ciudadano queda creado con el tipo de identidad correcto y el motivo de ausencia de DNI correspondiente.
