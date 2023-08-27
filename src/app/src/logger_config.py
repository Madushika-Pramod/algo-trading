import logging
import sys

from app.src.notify import news


class CustomHandler(logging.Handler):
    def emit(self, record):
        log_data = self.format(record)
        news(log_data)


# Create Logger and Set Level
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # or whatever level you want

# Configure File Handler
file_handler = logging.FileHandler('app.log')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Configure Stream Handler
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(levelname)s: %(message)s')
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

# Add Custom Handler
custom_handler = CustomHandler()
custom_handler.setFormatter(file_formatter)
custom_handler.setLevel(logging.ERROR)  # Set the level to ERROR
logger.addHandler(custom_handler)

# Store the original excepthook function
original_excepthook = sys.excepthook


def logging_excepthook(exc_type, exc_value, exc_traceback):
    logging.critical("Uncaught exception",
                     exc_info=(exc_type, exc_value, exc_traceback))
    # Use the original excepthook to print the exception to stderr (default behavior)
    original_excepthook(exc_type, exc_value, exc_traceback)


sys.excepthook = logging_excepthook
