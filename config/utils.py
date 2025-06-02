import os
import logging
from datetime import datetime
from pathlib import Path


class DailyFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        # Obtén la fecha actual
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Crea la carpeta basada en la fecha actual
        daily_folder = Path(filename).parent / current_date
        daily_folder.mkdir(parents=True, exist_ok=True)
        # Define el archivo dentro de la carpeta diaria
        daily_filename = daily_folder / Path(filename).name
        super().__init__(daily_filename, mode, encoding, delay)
