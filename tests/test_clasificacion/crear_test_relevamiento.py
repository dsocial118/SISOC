from comedores.models.comedor import Comedor
from comedores.models.relevamiento import (
    Anexo,
    CantidadColaboradores,
    Colaboradores,
    Espacio,
    EspacioCocina,
    EspacioPrestacion,
    Excepcion,
    FrecuenciaLimpieza,
    FrecuenciaRecepcionRecursos,
    FuenteCompras,
    FuenteRecursos,
    FuncionamientoPrestacion,
    MotivoExcepcion,
    Prestacion,
    PuntoEntregas,
    Relevamiento,
    TipoAccesoComedor,
    TipoAgua,
    TipoCombustible,
    TipoDeComedor,
    TipoDesague,
    TipoDistanciaTransporte,
    TipoEspacio,
    TipoFrecuenciaBolsones,
    TipoFrecuenciaInsumos,
    TipoGestionQuejas,
    TipoInsumos,
    TipoModalidadPrestacion,
    TipoModuloBolsones,
    TipoRecurso,
    TipoTecnologia,
)


def crear_test_relevamiento(
    sisoc_id,
    gestionar_uid,
    relevador,
    estado,
    fecha_visita,
    responsable_es_referente,
    responsable,
    territorial,
    funcionamiento,
    espacio,
    colaboradores_json,
    recursos,
    compras_jxon,
    prestacion,
    observacion,
    doc_pdf,
    anexo,
    excepcion,
    punto_entregas,
    imagenes_json,
):

    def create_tipo_recurso(nombre):
        if nombre:
            # Busca el recurso por nombre, si no existe, lo crea
            tipo_recurso = TipoRecurso.objects.get_or_create(nombre=nombre)
            return tipo_recurso
        return None  # Devuelve None si el nombre es vacío o None

    espacio_abastecimiento_agua = TipoAgua.objects.create(
        nombre=espacio["cocina"]["abastecimiento_agua"]
    )
    espacio_prestacio_frecuencia_limpieza = FrecuenciaLimpieza.objects.create(
        nombre=espacio["prestacion"]["frecuencia_limpieza"]
    )
    frecuencia_recepcion_recursos = FrecuenciaRecepcionRecursos.objects.create(
        nombre="Diaria"
    )

    # Manejar valores vacíos al crear TipoRecurso
    recursos_tipo_recursos_donaciones_particulares = create_tipo_recurso(
        recursos["recursos_donaciones_particulares"]
    )
    recursos_tipo_recursos_estado_nacional = create_tipo_recurso(
        recursos["recursos_estado_nacional"]
    )
    recursos_tipo_recursos_estado_provincial = create_tipo_recurso(
        recursos["recursos_estado_provincial"]
    )
    recursos_tipo_recursos_estado_municipal = create_tipo_recurso(
        recursos["recursos_estado_municipal"]
    )
    recursos_tipo_recursos_otros = create_tipo_recurso(recursos["recursos_otros"])

    frecuencia_tipo_bolsones = TipoFrecuenciaBolsones.objects.create(nombre="Diaria")

    fuente_recursos = FuenteRecursos.objects.create(
        recibe_donaciones_particulares=False,
        frecuencia_donaciones_particulares=frecuencia_recepcion_recursos,
        recibe_estado_nacional=False,
        frecuencia_estado_nacional=frecuencia_recepcion_recursos,
        recibe_estado_provincial=False,
        frecuencia_estado_provincial=frecuencia_recepcion_recursos,
        recibe_estado_municipal=False,
        frecuencia_estado_municipal=frecuencia_recepcion_recursos,
        recibe_otros=False,
        frecuencia_otros=frecuencia_recepcion_recursos,
    )
    fuente_recursos.recursos_donaciones_particulares.set(
        [recursos_tipo_recursos_donaciones_particulares]
    )
    fuente_recursos.recursos_estado_nacional.set(
        [recursos_tipo_recursos_estado_nacional]
    )
    fuente_recursos.recursos_estado_provincial.set(
        [recursos_tipo_recursos_estado_provincial]
    )
    fuente_recursos.recursos_estado_municipal.set(
        [recursos_tipo_recursos_estado_municipal]
    )
    fuente_recursos.recursos_otros.set([recursos_tipo_recursos_otros])

    punto_de_entrega = PuntoEntregas.objects.create(
        tipo_comedor=TipoDeComedor.objects.create(
            nombre=punto_entregas["tipo_comedor"]
        ),
        reciben_otros_recepcion=punto_entregas["reciben_otros_recepcion"],
        frecuencia_entrega_bolsones=frecuencia_tipo_bolsones,
        tipo_modulo_bolsones=TipoModuloBolsones.objects.create(
            nombre=punto_entregas["tipo_modulo_bolsones"]
        ),
        otros_punto_entregas=punto_entregas["otros_punto_entregas"],
        existe_punto_entregas=punto_entregas["existe_punto_entregas"],
        funciona_punto_entregas=punto_entregas["funciona_punto_entregas"],
        observa_entregas=punto_entregas["observa_entregas"],
        retiran_mercaderias_distribucion=punto_entregas[
            "retiran_mercaderias_distribucion"
        ],
        retiran_mercaderias_comercio=punto_entregas["retiran_mercaderias_comercio"],
        reciben_dinero=punto_entregas["reciben_dinero"],
        registran_entrega_bolsones=punto_entregas["registran_entrega_bolsones"],
    )
    punto_de_entrega.frecuencia_recepcion_mercaderias.set([frecuencia_tipo_bolsones])

    espacio_cocina = EspacioCocina.objects.create(
        espacio_elaboracion_alimentos=espacio["cocina"][
            "espacio_elaboracion_alimentos"
        ],
        almacenamiento_alimentos_secos=espacio["cocina"][
            "almacenamiento_alimentos_secos"
        ],
        heladera=espacio["cocina"]["heladera"],
        freezer=espacio["cocina"]["freezer"],
        recipiente_residuos_organicos=espacio["cocina"][
            "recipiente_residuos_organicos"
        ],
        recipiente_residuos_reciclables=espacio["cocina"][
            "recipiente_residuos_reciclables"
        ],
        otros_residuos=espacio["cocina"]["otros_residuos"],
        recipiente_otros_residuos=espacio["cocina"]["recipiente_otros_residuos"],
        instalacion_electrica=espacio["cocina"]["instalacion_electrica"],
        abastecimiento_agua=espacio_abastecimiento_agua,
        abastecimiento_agua_otro=espacio["cocina"]["abastecimiento_agua_otro"],
    )
    tipo_combustible = TipoCombustible.objects.create(
        nombre=espacio["cocina"]["abastecimiento_combustible"]
    )
    espacio_cocina.abastecimiento_combustible.set([tipo_combustible])

    espacio_prestacion = EspacioPrestacion.objects.create(
        espacio_equipado=espacio["prestacion"]["espacio_equipado"],
        tiene_ventilacion=espacio["prestacion"]["tiene_ventilacion"],
        tiene_salida_emergencia=espacio["prestacion"]["tiene_salida_emergencia"],
        salida_emergencia_senializada=espacio["prestacion"][
            "salida_emergencia_senializada"
        ],
        tiene_equipacion_incendio=espacio["prestacion"]["tiene_equipacion_incendio"],
        tiene_botiquin=espacio["prestacion"]["tiene_botiquin"],
        tiene_buena_iluminacion=espacio["prestacion"]["tiene_buena_iluminacion"],
        tiene_sanitarios=espacio["prestacion"]["tiene_sanitarios"],
        desague_hinodoro=TipoDesague.objects.create(
            nombre=espacio["prestacion"]["desague_hinodoro"]
        ),
        gestion_quejas=TipoGestionQuejas.objects.create(
            nombre=espacio["prestacion"]["gestion_quejas"]
        ),
        gestion_quejas_otro=espacio["prestacion"]["gestion_quejas_otro"],
        informacion_quejas=espacio["prestacion"]["informacion_quejas"],
        frecuencia_limpieza=espacio_prestacio_frecuencia_limpieza,
    )

    espacio_tipo_espacio_fisico = TipoEspacio.objects.create(
        nombre=espacio["tipo_espacio_fisico"]
    )
    comedor_test = Comedor.objects.create(
        nombre="Comedor Test",
        organizacion=None,
        programa=None,
        id_externo=None,
        comienzo=None,
        tipocomedor=None,
        calle=None,
        numero=None,
        piso=None,
        departamento=None,
        manzana=None,
        lote=None,
        entre_calle_1=None,
        entre_calle_2=None,
        latitud=None,
        longitud=None,
        provincia=None,
        municipio=None,
        localidad=None,
        partido=None,
        barrio=None,
        codigo_postal=None,
        referente=None,
        foto_legajo=None,
    )

    relevamiento = Relevamiento.objects.create(
        estado=estado,
        comedor=comedor_test,
        fecha_visita=fecha_visita,
        territorial_nombre=None,
        territorial_uid=None,
        funcionamiento=FuncionamientoPrestacion.objects.create(
            modalidad_prestacion=TipoModalidadPrestacion.objects.create(
                nombre=funcionamiento["modalidad_prestacion"]
            ),
            servicio_por_turnos=funcionamiento["servicio_por_turnos"],
        ),
        espacio=Espacio.objects.create(
            tipo_espacio_fisico=espacio_tipo_espacio_fisico,
            espacio_fisico_otro=espacio["espacio_fisico_otro"],
            cocina=espacio_cocina,
            prestacion=espacio_prestacion,
        ),
        colaboradores=Colaboradores.objects.create(
            cantidad_colaboradores=CantidadColaboradores.objects.create(
                nombre=colaboradores_json["cantidad_colaboradores"],
            ),
            colaboradores_capacitados_alimentos=colaboradores_json[
                "colaboradores_capacitados_alimentos"
            ],
            colaboradores_recibieron_capacitacion_alimentos=colaboradores_json[
                "colaboradores_recibieron_capacitacion_alimentos"
            ],
            colaboradores_capacitados_salud_seguridad=colaboradores_json[
                "colaboradores_capacitados_salud_seguridad"
            ],
            colaboradores_recibieron_capacitacion_emergencias=colaboradores_json[
                "colaboradores_recibieron_capacitacion_emergencias"
            ],
            colaboradores_recibieron_capacitacion_violencia=colaboradores_json[
                "colaboradores_recibieron_capacitacion_violencia"
            ],
        ),
        recursos=fuente_recursos,
        compras=FuenteCompras.objects.create(
            almacen_cercano=compras_jxon["almacen_cercano"],
            verduleria=compras_jxon["verduleria"],
            carniceria=compras_jxon["carniceria"],
            granja=compras_jxon["granja"],
            pescaderia=compras_jxon["pescaderia"],
            supermercado=compras_jxon["supermercado"],
            mercado_central=compras_jxon["mercado_central"],
            ferias_comunales=compras_jxon["ferias_comunales"],
            mayoristas=compras_jxon["mayoristas"],
            otro=compras_jxon["otro"],
        ),
        prestacion=Prestacion.objects.create(
            lunes_desayuno_actual=prestacion["lunes_desayuno_actual"],
            lunes_desayuno_espera=prestacion["lunes_desayuno_espera"],
            lunes_almuerzo_actual=prestacion["lunes_almuerzo_actual"],
            lunes_almuerzo_espera=prestacion["lunes_almuerzo_espera"],
            lunes_merienda_actual=prestacion["lunes_merienda_actual"],
            lunes_merienda_espera=prestacion["lunes_merienda_espera"],
            lunes_cena_actual=prestacion["lunes_cena_actual"],
            lunes_cena_espera=prestacion["lunes_cena_espera"],
            martes_desayuno_actual=prestacion["martes_desayuno_actual"],
            martes_desayuno_espera=prestacion["martes_desayuno_espera"],
            martes_almuerzo_actual=prestacion["martes_almuerzo_actual"],
            martes_almuerzo_espera=prestacion["martes_almuerzo_espera"],
            martes_merienda_actual=prestacion["martes_merienda_actual"],
            martes_merienda_espera=prestacion["martes_merienda_espera"],
            martes_cena_actual=prestacion["martes_cena_actual"],
            martes_cena_espera=prestacion["martes_cena_espera"],
            miercoles_desayuno_actual=prestacion["miercoles_desayuno_actual"],
            miercoles_desayuno_espera=prestacion["miercoles_desayuno_espera"],
            miercoles_almuerzo_actual=prestacion["miercoles_almuerzo_actual"],
            miercoles_almuerzo_espera=prestacion["miercoles_almuerzo_espera"],
            miercoles_merienda_actual=prestacion["miercoles_merienda_actual"],
            miercoles_merienda_espera=prestacion["miercoles_merienda_espera"],
            miercoles_cena_actual=prestacion["miercoles_cena_actual"],
            miercoles_cena_espera=prestacion["miercoles_cena_espera"],
            jueves_desayuno_actual=prestacion["jueves_desayuno_actual"],
            jueves_desayuno_espera=prestacion["jueves_desayuno_espera"],
            jueves_almuerzo_actual=prestacion["jueves_almuerzo_actual"],
            jueves_almuerzo_espera=prestacion["jueves_almuerzo_espera"],
            jueves_merienda_actual=prestacion["jueves_merienda_actual"],
            jueves_merienda_espera=prestacion["jueves_merienda_espera"],
            jueves_cena_actual=prestacion["jueves_cena_actual"],
            jueves_cena_espera=prestacion["jueves_cena_espera"],
            viernes_desayuno_actual=prestacion["viernes_desayuno_actual"],
            viernes_desayuno_espera=prestacion["viernes_desayuno_espera"],
            viernes_almuerzo_actual=prestacion["viernes_almuerzo_actual"],
            viernes_almuerzo_espera=prestacion["viernes_almuerzo_espera"],
            viernes_merienda_actual=prestacion["viernes_merienda_actual"],
            viernes_merienda_espera=prestacion["viernes_merienda_espera"],
            viernes_cena_actual=prestacion["viernes_cena_actual"],
            viernes_cena_espera=prestacion["viernes_cena_espera"],
            sabado_desayuno_actual=prestacion["sabado_desayuno_actual"],
            sabado_desayuno_espera=prestacion["sabado_desayuno_espera"],
            sabado_almuerzo_actual=prestacion["sabado_almuerzo_actual"],
            sabado_almuerzo_espera=prestacion["sabado_almuerzo_espera"],
            sabado_merienda_actual=prestacion["sabado_merienda_actual"],
            sabado_merienda_espera=prestacion["sabado_merienda_espera"],
            sabado_cena_actual=prestacion["sabado_cena_actual"],
            sabado_cena_espera=prestacion["sabado_cena_espera"],
            domingo_desayuno_actual=prestacion["domingo_desayuno_actual"],
            domingo_desayuno_espera=prestacion["domingo_desayuno_espera"],
            domingo_almuerzo_actual=prestacion["domingo_almuerzo_actual"],
            domingo_almuerzo_espera=prestacion["domingo_almuerzo_espera"],
            domingo_merienda_actual=prestacion["domingo_merienda_actual"],
            domingo_merienda_espera=prestacion["domingo_merienda_espera"],
            domingo_cena_actual=prestacion["domingo_cena_actual"],
            domingo_cena_espera=prestacion["domingo_cena_espera"],
        ),
        punto_entregas=punto_de_entrega,
        excepcion=Excepcion.objects.create(
            motivo=MotivoExcepcion.objects.create(nombre="No hay personal"),
            descripcion=None,
            latitud=None,
            longitud=None,
            adjuntos=None,
            firma=None,
        ),
        anexo=Anexo.objects.create(
            tipo_insumo=TipoInsumos.objects.create(nombre="Alimentos"),
            frecuencia_insumo=TipoFrecuenciaInsumos.objects.create(nombre="Diaria"),
            tecnologia=TipoTecnologia.objects.create(nombre="Internet"),
            acceso_comedor=TipoAccesoComedor.objects.create(nombre="Caminando"),
            distancia_transporte=TipoDistanciaTransporte.objects.create(
                nombre="Menos de 5 cuadras"
            ),
            comedor_merendero=anexo["comedor_merendero"],
            insumos_organizacion=anexo["insumos_organizacion"],
            servicio_internet=anexo["servicio_internet"],
            zona_inundable=anexo["zona_inundable"],
            actividades_jardin_maternal=anexo["actividades_jardin_maternal"],
            actividades_jardin_infantes=anexo["actividades_jardin_infantes"],
            apoyo_escolar=anexo["apoyo_escolar"],
            alfabetizacion_terminalidad=anexo["alfabetizacion_terminalidad"],
            capacitaciones_talleres=anexo["capacitaciones_talleres"],
            promocion_salud=anexo["promocion_salud"],
            actividades_discapacidad=anexo["actividades_discapacidad"],
            necesidades_alimentarias=anexo["necesidades_alimentarias"],
            actividades_recreativas=anexo["actividades_recreativas"],
            actividades_culturales=anexo["actividades_culturales"],
            emprendimientos_productivos=anexo["emprendimientos_productivos"],
            actividades_religiosas=anexo["actividades_religiosas"],
            actividades_huerta=anexo["actividades_huerta"],
            espacio_huerta=anexo["espacio_huerta"],
            otras_actividades=anexo["otras_actividades"],
            cuales_otras_actividades=anexo["cuales_otras_actividades"],
            veces_recibio_insumos_2024=anexo["veces_recibio_insumos_2024"],
        ),
        imagenes=imagenes_json,
        observacion=observacion,
        docPDF=doc_pdf,
        responsable_es_referente=responsable_es_referente,
        responsable_relevamiento=None,
    )

    return relevamiento
