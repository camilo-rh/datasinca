import logging
from datetime import datetime
from termcolor import colored
from pathlib import Path

def get_log_dir():
    home = Path.home()
    log_dir = home / ".datasinca" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': 'blue',
        'INFO': 'white',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }

    def format(self, record):
        msg = super().format(record)
        color = self.COLORS.get(record.levelname, 'white')
        return colored(msg, color)


def setup_logging(name="datasinca", log_dir=None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # capturar todo internamente

    # evitar duplicados
    if logger.handlers:
        return logger

    if log_dir is None:
        log_dir = get_log_dir()

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{name}_{timestamp}.log"

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter( ColoredFormatter("%(levelname)s: %(message)s") )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter( logging.Formatter( "%(asctime)s | %(levelname)s | %(message)s" ) )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    print(f"Logging iniciado: {log_file}")

    return logger