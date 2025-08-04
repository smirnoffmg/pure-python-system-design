import logging
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    # Create a logger object
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Set the default log level to INFO

    # Check if the logger already has handlers to avoid duplicate logs
    if len(logger.handlers) == 0:
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a rotating file handler
        file_handler = RotatingFileHandler(
            "app.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,  # Keep up to 3 backup files
        )
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter and set it for both handlers
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


logger = get_logger(__name__)
