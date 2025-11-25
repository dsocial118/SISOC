# Archivo temporal para reemplazar importacion_service.py
# Contiene solo la sección de creación de relaciones familiares corregida

# REEMPLAZAR la sección de "Crear relaciones familiares" con esto:

                # Crear relaciones familiares
                if relaciones_familiares:
                    try:
                        from ciudadanos.models import GrupoFamiliar

                        relaciones_crear = []
                        for rel in relaciones_familiares:
                            try:
                                relaciones_crear.append(
                                    GrupoFamiliar(
                                        ciudadano_1_id=rel["responsable_id"],
                                        ciudadano_2_id=rel["hijo_id"],
                                        vinculo=GrupoFamiliar.RELACION_PADRE,
                                        conviven=True,
                                        cuidador_principal=True,
                                    )
                                )
                            except Exception as e:
                                logger.error(
                                    "Error preparando relacion familiar fila %s: %s",
                                    rel["fila"],
                                    e,
                                )

                        if relaciones_crear:
                            GrupoFamiliar.objects.bulk_create(
                                relaciones_crear,
                                batch_size=batch_size,
                                ignore_conflicts=True,
                            )
                            logger.info(
                                "Creadas %s relaciones familiares",
                                len(relaciones_crear),
                            )
                    except Exception as e:
                        logger.error("Error creando relaciones familiares: %s", e)
                        warnings.append(
                            {
                                "fila": "general",
                                "campo": "relaciones_familiares",
                                "detalle": f"Error creando relaciones: {str(e)}",
                            }
                        )
