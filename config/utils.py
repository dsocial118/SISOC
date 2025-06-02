import logging
from datetime import datetime
from pathlib import Path


class DailyFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        current_date = datetime.now().strftime("%Y-%m-%d")
        daily_folder = Path(filename).parent / current_date
        daily_folder.mkdir(parents=True, exist_ok=True)
        daily_filename = daily_folder / Path(filename).name
        super().__init__(daily_filename, mode, encoding, delay)
