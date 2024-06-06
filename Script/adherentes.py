import numpy as np
import pandas as pd

from sqlalchemy import Column, String, Integer, Date, text, BigInteger, DateTime
from sqlalchemy import create_engine, MetaData
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, declarative_base


# Function to parse the fixed width text file
def parse_fixed_width_text(filename):
    # Define column widths
    widths = [11, 10, 2, 10, 2, 11, 2, 40, 10, 2, 10]

    # Read the file using fixed width parsing
    df = pd.read_fwf(filename, widths=widths, header=None,  encoding='latin1')

    # Set column names
    df.columns = ['CUIL', 'FECHA_NACIMIENTO', 'COD_FALLECIMIENTO', 'FECHA_FALLECIMIENTO', 'CANTIDAD_HIJO', 'CUIL_RELACIONADO',
                  'COD_RELACION', 'APELLIDO_NOMBRE', 'FECHA_NACIMIENTO2', 'COD_FALLECIMIENTO2', 'FECHA_FALLECIMIENTO2']
    return df

# Read the fixed width text file
filename = r'C:/Users/MDS/Downloads/SALEOK.F240404.txt'
data_df = parse_fixed_width_text(filename)

def split_name_fullname(fullname):
    # split the fullname into words
    words = fullname.split(" ")

    # check if there are at least 4 words (minimum for two last names and two first names)
    if len(words) < 1:
        return None, None

    # Splitting the surnames and names
    surnames = words[:1]  # First 2 words are surnames
    first_names = words[1:]  # Remaining words are names

    # Join the surnames
    joined_surnames = ' '.join(surnames)

    # Join the first names
    joined_first_names = ' '.join(first_names)

    return joined_surnames, joined_first_names




# Convert data types
data_df['CUIL'] = data_df['CUIL'].astype(float).astype('Int64')
data_df['FECHA_NACIMIENTO'] = pd.to_datetime(data_df['FECHA_NACIMIENTO'], format='%d.%m.%Y')
data_df['COD_FALLECIMIENTO'] = pd.to_numeric(data_df['COD_FALLECIMIENTO'], errors='coerce')
data_df['FECHA_FALLECIMIENTO'] = pd.to_datetime(data_df['FECHA_FALLECIMIENTO'], format='%d.%m.%Y')
data_df['CANTIDAD_HIJO'] = data_df['CANTIDAD_HIJO'].astype(float).astype('Int64')
data_df['CUIL_RELACIONADO'] = data_df['CUIL_RELACIONADO'].astype(float).astype('Int64')
data_df['COD_RELACION'] = data_df['COD_RELACION'].astype(float).astype('Int64')
data_df['APELLIDO_NOMBRE'] = data_df['APELLIDO_NOMBRE'].astype(str)
data_df['APELLIDO'], data_df['NONMBRE'] = zip(*data_df['APELLIDO_NOMBRE'].apply(split_name_fullname))

data_df['FECHA_NACIMIENTO2'] = pd.to_datetime(data_df['FECHA_NACIMIENTO2'], format='%d.%m.%Y')
data_df['COD_FALLECIMIENTO2'] = pd.to_numeric(data_df['COD_FALLECIMIENTO2'], errors='coerce')
data_df['FECHA_FALLECIMIENTO2'] = pd.to_datetime(data_df['FECHA_FALLECIMIENTO2'], format='%d.%m.%Y')

# # Replace '\x00\x00' with None
# data_df = data_df.replace('\x00\x00', None)
# data_df = data_df.where(pd.notnull(data_df), np.nan)
# df = data_df.where(pd.notnull(data_df), None)
#
# # Replace NaN and '\x00\x00' values
# data_df.replace({np.nan: 0, '\x00\x00': 0}, inplace=True)
#
# # Replace NaN values
# data_df.fillna({'CUIL': 0, 'FECHA_NACIMIENTO': pd.NaT, 'COD_FALLECIMIENTO':0,
#                 'FECHA_FALLECIMIENTO':  pd.NaT, 'CANTIDAD_HIJO':0, 'CUIL_RELACIONADO':0,
#                 'COD_RELACION':0, 'APELLIDO_NOMBRE':'','FECHA_NACIMIENTO2': pd.NaT, 'COD_FALLECIMIENTO2':0, 'FECHA_FALLECIMIENTO2': pd.NaT},inplace=True)

# SSH settings
# ssh_host = '10.80.9.15'
# ssh_port = 22
# ssh_username = 'admin-ssies'
# ssh_password = 'aqV0hqqy0r'


# Establish SSH connection
# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)


# Define the base
Base = declarative_base()

# Create the engine
#engine = create_engine('mysql+mysqlconnector://admin-ssies:aqV0hqqy0r@10.80.9.15:3306/pas_padron_01_05_2024', connect_args={'connect_timeout': 288000}, pool_pre_ping=True)
# Valores de conexión a la base de datos
username = 'root'
password = 'matias123'
host = 'localhost'
port = '3306'  # Asegúrate de que este valor sea un número entero
database = 'sisocdev'

# Crear la cadena de conexión con los valores interpolados usando f-strings
connection_string = f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}'

# Crear el motor de SQLAlchemy
engine = create_engine(connection_string, connect_args={'connect_timeout': 288000}, pool_pre_ping=True)

# Define the database connection

connect_args = {'connect_timeout': 28800}
pool_pre_ping = True
# Create tables
Base.metadata.create_all(engine)
# Commit DataFrame to MySQL database

data_df.to_sql(
    name='adherentes',
    con=engine,
    if_exists='replace',
    index=False,
    method='multi',  # Use the 'multi' insert method for better performance
    chunksize=1000  # Commit data in chunks of 1000 rows for better memory management
)



