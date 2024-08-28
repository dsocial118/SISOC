import pandas as pd

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Date,
    CHAR,
    ForeignKey,
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from sqlalchemy.exc import OperationalError
import time

# Define the database connection
engine = create_engine(f"mysql+mysqlconnector://root:matias123@localhost:3306/hsudev")

# Define the ORM Base
Base = declarative_base()

from sqlalchemy.exc import OperationalError
import time

max_retries = 3
retry_delay = 1  # seconds

# Replace 'your_file.csv' with the path to your CSV file
file_path = r"C:\Users\MDS\Downloads\cruce_nomina_pas (4).csv"

# Read the CSV file into a DataFrame with specified column names
data = pd.read_csv(file_path, sep="|")


# Define the table classes
class Person(Base):
    __tablename__ = "beneficiario_padron"

    CUIT = Column(String(255), primary_key=True, autoincrement=False)
    _id = Column(String(255))
    fechaAlta = Column(String(255))
    cuil = Column(String(255))
    dniNumero = Column(String(255))
    nombre = Column(String(255))
    apellido = Column(String(255))
    identidad = Column(String(255))
    sexo = Column(CHAR(1))
    fechaNacimiento = Column(String(255))
    nacionalidad = Column(String(255))
    pais = Column(String(255))
    provincia = Column(String(255))
    localidad = Column(String(255))
    municipio = Column(String(255))
    cp = Column(String(255))
    barrio = Column(String(255))
    calle = Column(String(255))
    numero = Column(String(255))
    piso = Column(String(255))
    manzana = Column(String(255))
    observaciones = Column(String(255))
    tieneHijos = Column(String(255))
    tieneCud = Column(String(255))
    cantidadHijos = Column(String(255))
    presentaDiscapacidad = Column(String(255))
    cantidadPresentaDiscapacidad = Column(String(255))
    email = Column(String(255))
    prefijo = Column(String(10))
    telefono = Column(String(20))
    prefijoAlt = Column(String(10))
    telefonoAlt = Column(String(20))
    nivelEstudioAlcanzado = Column(String(255))
    nombreInstitucion = Column(String(255))
    provinciaInstitucion = Column(String(100))
    localidadInstitucion = Column(String(100))
    municipioInstitucion = Column(String(100))
    barrioInstitucion = Column(String(100))
    calleInstitucion = Column(String(255))
    numeroInstitucion = Column(String(10))
    interesEstudio = Column(String(255))
    interesCurso = Column(String(255))
    principalActividad = Column(String(255))
    actividadesProductivas = Column(String(255))
    nivelEstudio = Column(String(255))
    noSabeNombreInstitucion = Column(String(255))
    noSabeDomicilioInstitucion = Column(String(255))
    interesSeguirActividad = Column(String(255))
    cualInteresaSeguir = Column(String(255))
    cobrasPotenciarTrabajo = Column(String(255))
    modalidadCobro = Column(String(255))
    otraModalidadCobro = Column(String(255))
    conocesUindadGestion = Column(String(255))
    nombreUnidadGestion = Column(String(255))


# Create tables
Base.metadata.create_all(engine)

# Start a session
Session = sessionmaker(bind=engine)
session = Session()

# Convert DataFrame to dictionaries
data_dict = data.to_dict(orient="records")


# Replace nan values with None
for d in data_dict:
    for key, value in d.items():
        if pd.isna(value):
            d[key] = None

# Insert data into the database
for row in data_dict:

    # Create Person object
    person_data = {key: row[key] for key in row.keys()}  # Filter keys to match columns
    person = Person(**person_data)

    # Add to session and flush
    for retry in range(max_retries):
        try:
            session.add(person)
            session.flush()
            break  # Operation succeeded, exit the loop
        except OperationalError as e:
            if retry == max_retries - 1:
                raise  # Max retries reached, raise the exception
            print(
                f"Retry {retry + 1}: Lock wait timeout exceeded. Retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            session.rollback()


# Commit changes and close session
session.commit()
session.close()

# Commit changes and close session
session.commit()
session.close()
