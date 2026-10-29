import logging


def setup_logger(name: str, level: int = logging.INFO):
    """
    Set up a basic stdout logging configuration.

    Usage: `logger = setup_logger(__name__)`.

    Args:
        name (str): Module `__name__` to ensure logs are traceable to their
            source code location.
        level (int): Root logger logging level. Ranges from 0 to 50.
            (DEBUG | INFO | WARNING | ERROR | CRITICAL).

    Returns:
        Logger (logging.Logger): An instance of the configured logging class.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S%z",
    )

    return logging.getLogger(name)
