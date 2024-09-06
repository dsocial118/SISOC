--Beneficiaros
INSERT INTO sisoc.Legajos_legajos (
    _id,
    APELLIDO,
    NOMBRE,
    FECHA_NACIMIENTO,
    TIPO_DOC,
    DOCUMENTO,
    SEXO,
    NACIONALIDAD,
    ESTADO_CIVIL,
    CALLE,
    ALTURA,
    PISO,
    CIRCUITO,
    BARRIO,
    LOCALIDAD,
    TELEFONO,
    EMAIL,
    FOTO,
    OBSERVACIONES,
    ESTADO,
    CREADO,
    MODIFICADO,
    CREADO_POR_ID,
    MODIFICADO_POR_ID,
    CUIT,
    CUIL,
    IDENTIDAD,
    PROVINCIA,
    PAIS,
    MUNICIPIO,
    CP,
    MANZANA,
    PREFIJO_TEL2,
    TELEFONO2,
    PREFIJO_TEL_ALT,
    TELEFONO_ALT,
    OBSERVACIONES_BENEF,
    TIENE_HIJOS,
    TIENE_CUD,
    CANTIDAD_HIJOS,
    PRESENTA_DISCAPACIDAD,
    CANTIDAD_PRESENTA_DISCAPACIDAD,
    MODALIDAD_COBRO,
    OTRA_MODALIDAD_COBRO
)
SELECT
    bp._id,
    COALESCE(bp.apellido, 'xxxx') AS APELLIDO,
    COALESCE(bp.nombre, 'xxxx') AS APELLIDO,
    COALESCE(STR_TO_DATE(bp.fechaNacimiento, '%d/%m/%Y'), NOW()) AS FECHA_NACIMIENTO, -- Corrected date format
    null AS TIPO_DOC,
    bp.dniNumero AS DOCUMENTO,
    COALESCE(bp.sexo, 'beneficiarios') AS SEXO,
    bp.nacionalidad,
    null AS ESTADO_CIVIL,
    bp.calle,
    bp.numero AS ALTURA,
    bp.pisodpto AS PISO_DPTO,
    null AS CIRCUITO,
    bp.barrio,
    bp.localidad,
    bp.codigopostal,
    bp.torrepasillo,
    bp.escaleramanzana,
    bp.telefono,
    bp.email,
    null AS FOTO,
    null AS OBSERVACIONES,
    1 AS ESTADO,
    NOW() AS CREADO,
    NOW() AS MODIFICADO,
    null AS CREADO_POR_ID,
    null AS MODIFICADO_POR_ID,
    bp.CUIT,
    bp.CUIL,
    bp.IDENTIDAD,
    bp.PROVINCIA,
    bp.PAIS,
    bp.MUNICIPIO,
    bp.CP,
    bp.MANZANA,
    bp.PREFIJO AS PREFIJO_TEL2,
    bp.TELEFONO AS TELEFONO2,
    bp.prefijoalt AS PREFIJO_TEL_ALT,
    bp.telefonoalt AS TELEFONO_ALT,
    bp.observaciones AS OBSERVACIONES_BENEF,
    bp.tienehijos AS TIENE_HIJOS,
    bp.tienecud AS TIENE_CUD,
    bp.cantidadhijos AS CANTIDAD_HIJOS,
    bp.PRESENTADISCAPACIDAD AS PRESENTA_DISCAPACIDAD,
    bp.CANTIDADPRESENTADISCAPACIDAD AS CANTIDAD_PRESENTA_DISCAPACIDAD,
    bp.MODALIDADCOBRO AS MODALIDAD_COBRO,
    bp.OTRAMODALIDADCOBRO AS OTRA_MODALIDAD_COBRO
FROM sisoc.beneficiario_padron bp;



--Aderentes

INSERT IGNORE INTO sisoc.Legajos_legajos (
  _id,
  apellido,
  nombre,
  fecha_nacimiento,
  tipo_doc,
  documento,
  sexo,
  nacionalidad,
  estado_civil,
  calle,
  altura,
  piso,
  circuito,
  barrio,
  localidad,
  telefono,
  email,
  foto,
  observaciones,
  estado,
  creado,
  modificado,
  creado_por_id,
  modificado_por_id,
  cuit,
  identidad,
  provincia,
  pais,
  municipio,
  cp,
  manzana,
  prefijo_tel2,
  telefono2,
  prefijo_tel_alt,
  telefono_alt,
  observaciones_benef,
  tiene_Hijos,
  tiene_Cud,
  cantidad_Hijos,
  presenta_Discapacidad,
  cantidad_Presenta_Discapacidad,
  modalidad_Cobro,
  otra_Modalidad_Cobro
)
SELECT
  NULL as _id,
  a.APELLIDO as apellido,
  a.NONMBRE as nombre,
  a.FECHA_NACIMIENTO2 as fecha_nacimiento,
  '' as tipo_doc,
  a.CUIL_RELACIONADO as documento,
  'Aderente' as sexo,
  '' as nacionalidad,
  '' as estado_civil,
  '' as calle,
  NULL as altura,
  '' as pisodpto,
  '' as circuito,
  '' as barrio,
  '' as localidad,
  NULL as telefono,
  '' as email,
  '' as foto,
  '' as observaciones,
  1 as estado,
  NOW() as creado,
  NOW() as modificado,
  NULL as creado_por_id,
  NULL as modificado_por_id,
  a.CUIL as cuit,
  '' as identidad,
  '' as provincia,
  '' as pais,
  '' as municipio,
  '' as cp,
  '' as manzana,
  '' as prefijo_tel2,
  '' as telefono2,
  '' as prefijo_tel_alt,
  '' as telefono_alt,
  '' as observaciones_benef,
  '' as tiene_Hijos,
  '' as tiene_Cud,
  NULL as cantidad_Hijos,
  '' as presenta_Discapacidad,
  '' as cantidad_Presenta_Discapacidad,
  '' as modalidad_Cobro,
  '' as otra_Modalidad_Cobro
FROM
  sisoc.adherentes a
WHERE
  a.CUIL IS NOT NULL
  AND a.COD_RELACION IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM sisoc.Legajos_legajos ll
    WHERE ll.documento = a.CUIL_RELACIONADO
  );