import logging


def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # You can also add more advanced configurations here,
    # like setting up loggers, handlers, and formatters.
