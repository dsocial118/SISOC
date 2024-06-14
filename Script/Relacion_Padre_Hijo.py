from sqlalchemy import create_engine, MetaData
import pandas as pd

def main():
    # Configura los motores de base de datos
    engine_pas_padron_01_05_2024 = create_engine('mysql://root:admin@localhost:3306/pas_padron_01_05_2024')  # Cambia con tu URL de base de datos
    engine_hsu_dev = create_engine('mysql://root:admin@localhost:3306/hsu-dev')  # Cambia con tu URL de base de datos

    # Vincula una conexión
    connection_hsu_dev = engine_hsu_dev.connect()
    connection_pas_padron_01_05_2024 = engine_pas_padron_01_05_2024.connect()

    # Carga los metadatos
    metadata = MetaData()

    # Consulta para obtener los beneficiarios del padrón
    query = """
        SELECT
            bp._id, COALESCE(bp.apellido, 'xxxx') AS APELLIDO, COALESCE(bp.nombre, 'xxxx') AS NOMBRE,
            COALESCE(STR_TO_DATE(bp.fechaNacimiento, '%%d/%%m/%%Y'), NOW()) AS FECHA_NACIMIENTO,
            'CUIT' AS TIPO_DOC, bp.dniNumero AS DOCUMENTO,
            CASE WHEN COALESCE(bp.sexo, 'X') = 'M' THEN 'Masculino' WHEN COALESCE(bp.sexo, 'X') = 'F' THEN 'Femenino' ELSE 'X' END AS SEXO,
            bp.nacionalidad, null AS ESTADO_CIVIL, bp.calle, bp.numero AS ALTURA, bp.piso, null AS CIRCUITO,
            bp.barrio, bp.localidad, bp.telefono, bp.email, null AS FOTO,
            null AS OBSERVACIONES, 1 AS ESTADO, NOW() AS CREADO,
            NOW() AS MODIFICADO, null AS CREADO_POR_ID, null AS MODIFICADO_POR_ID, bp.CUIT, bp.CUIL,
            bp.IDENTIDAD, bp.PROVINCIA, bp.PAIS, bp.MUNICIPIO, bp.CP, bp.MANZANA, bp.PREFIJO AS PREFIJO_TEL2,
            bp.TELEFONO AS TELEFONO2, bp.prefijoalt AS PREFIJO_TEL_ALT, bp.telefonoalt AS TELEFONO_ALT,
            bp.observaciones AS OBSERVACIONES_BENEF,
            bp.tienehijos AS TIENE_HIJOS, bp.tienecud AS TIENE_CUD, bp.cantidadhijos AS CANTIDAD_HIJOS,
            bp.PRESENTADISCAPACIDAD AS PRESENTA_DISCAPACIDAD,
            bp.CANTIDADPRESENTADISCAPACIDAD AS CANTIDAD_PRESENTA_DISCAPACIDAD,
            bp.MODALIDADCOBRO AS MODALIDAD_COBRO, bp.OTRAMODALIDADCOBRO AS OTRA_MODALIDAD_COBRO
        FROM beneficiario_padron bp
    """

    # Consulta para obtener los adherentes
    query_adherentes = """
        SELECT
           null as _id, a.APELLIDO as APELLIDO, a.NOMBRE as NOMBRE,
           a.FECHA_NACIMIENTO2 as 'FECHA_NACIMIENTO', '' as TIPO_DOC,
           null as DOCUMENTO, 'U' as SEXO, '' as NACIONALIDAD,
           '' as ESTADO_CIVIL, '' as CALLE, null as ALTURA,
           '' as PISO, '' as CIRCUITO, '' as BARRIO, '' as LOCALIDAD,
           null as TELEFONO, '' as EMAIL, '' as FOTO, '' as OBSERVACIONES,
           1 as ESTADO, NOW() as CREADO, NOW() as MODIFICADO, null as CREADO_POR_ID,
           null as MODIFICADO_POR_ID, null as CUIT, a.CUIL_RELACIONADO as CUIL,
           '' as IDENTIDAD, '' as PROVINCIA, '' as PAIS, '' as MUNICIPIO,
           '' as CP, '' as MANZANA, '' as PREFIJO_TEL2, '' as TELEFONO2,
           '' as PREFIJO_TEL_ALT, '' as TELEFONO_ALT, '' as OBSERVACIONES_BENEF,
           '' as TIENE_HIJOS, '' as TIENE_CUD, null as CANTIDAD_HIJOS,
           '' as PRESENTA_DISCAPACIDAD, '' as CANTIDAD_PRESENTA_DISCAPACIDAD,
           '' as MODALIDAD_COBRO, '' as OTRA_MODALIDAD_COBRO
        FROM adherentes a
    """

    # Leer los datos de las consultas
    df_beneficiario_padron = pd.read_sql(query, connection_pas_padron_01_05_2024)
    df_adherentes = pd.read_sql(query_adherentes, connection_pas_padron_01_05_2024)

    # Insertar datos en la tabla Legajos_legajos
    df_beneficiario_padron.to_sql('Legajos_legajos', con=connection_hsu_dev, if_exists='append', index=False)
    df_adherentes.to_sql('Legajos_legajos', con=connection_hsu_dev, if_exists='append', index=False)

    # Leer los datos insertados para realizar operaciones adicionales
    df_legajos_legajos = pd.read_sql('SELECT * FROM Legajos_legajos', connection_hsu_dev)

    # Generar grupos familiares
    df_grupos_familiares = df_legajos_legajos.groupby('CUIL').agg({
        '_id': 'first',
        'APELLIDO': 'first',
        'NOMBRE': 'first',
        'FECHA_NACIMIENTO': 'first',
        'TIPO_DOC': 'first',
        'DOCUMENTO': 'first',
        'SEXO': 'first',
        'nacionalidad': 'first',
        'ESTADO_CIVIL': 'first',
        'calle': 'first',
        'ALTURA': 'first',
        'piso': 'first',
        'CIRCUITO': 'first',
        'barrio': 'first',
        'localidad': 'first',
        'telefono': 'first',
        'email': 'first',
        'FOTO': 'first',
        'OBSERVACIONES': 'first',
        'ESTADO': 'first',
        'CREADO': 'first',
        'MODIFICADO': 'first',
        'CREADO_POR_ID': 'first',
        'MODIFICADO_POR_ID': 'first',
        'CUIT': 'first',
        'CUIL': 'first',
        'IDENTIDAD': 'first',
        'PROVINCIA': 'first',
        'PAIS': 'first',
        'MUNICIPIO': 'first',
        'CP': 'first',
        'MANZANA': 'first',
        'PREFIJO_TEL2': 'first',
        'TELEFONO2': 'first',
        'PREFIJO_TEL_ALT': 'first',
        'TELEFONO_ALT': 'first',
        'OBSERVACIONES_BENEF': 'first',
        'TIENE_HIJOS': 'first',
        'TIENE_CUD': 'first',
        'CANTIDAD_HIJOS': 'first',
        'PRESENTA_DISCAPACIDAD': 'first',
        'CANTIDAD_PRESENTA_DISCAPACIDAD': 'first',
        'MODALIDAD_COBRO': 'first',
        'OTRA_MODALIDAD_COBRO': 'first'
    }).reset_index()

    # Insertar los grupos familiares en la tabla correspondiente
    df_grupos_familiares.to_sql('Legajos_legajogrupofamiliar', con=connection_hsu_dev, if_exists='append', index=False)

    print("Data inserted successfully in all tables!")
    print("Updated dataset successfully!")

    # Cerrar las conexiones
    connection_pas_padron_01_05_2024.close()
    connection_hsu_dev.close()

if __name__ == '__main__':
    main()
