from config import LOG_LEVEL
from loguru import logger
from sys import stdout


def formatter(log: dict) -> str:
    """ Format log colors based on level.

    :param log: dict, containing log level, details, etc.
    :returns: str,
    """
    if log["level"].name == "DEBUG":
        return (
            "<fg #f8ffe5>{time:HH:mm:ss A} | </fg #f8ffe5>"
            "<fg #1b9aaa>{level}</fg #1b9aaa>    | "
            "<fg #f8ffe5>{file}:{function}:{line} | </fg #f8ffe5>"
            "{message}\n"
        )
    if log["level"].name == "INFO":
        return (
            "<fg #f8ffe5>{time:HH:mm:ss A} | </fg #f8ffe5>"
            "{level}     | "
            "{message}\n"
        )
    if log["level"].name == "SUCCESS":
        return (
            "<fg #f8ffe5>{time:HH:mm:ss A} | </fg #f8ffe5>"
            "<fg #06d6a0>{level}</fg #06d6a0>  | "
            "{message}\n"
        )
    if log["level"].name == "WARNING":
        return (
            "<fg #f8ffe5>{time:HH:mm:ss A} | </fg #f8ffe5>"
            "<fg #ffc43d>{level}</fg #ffc43d>  | "
            "{message}\n"
        )
    if log["level"].name == "ERROR":
        return (
            "<fg #f8ffe5>{time:HH:mm:ss A} | </fg #f8ffe5>"
            "<fg #ef476f>{level}</fg #ef476f>    | "
            "<fg #f8ffe5>{file}:{function}:{line} | </fg #f8ffe5>"
            "{message}\n"
        )
    if log["level"].name == "CRITICAL":
        return (
            "<fg #f8ffe5>{time:HH:mm:ss A} | </fg #f8ffe5>"
            "<bg #ef476f>{level}</bg #ef476f> | "
            "<fg #f8ffe5>{file}:{function}:{line} | </fg #f8ffe5>"
            "{message}\n"
        )


def configure_logger() -> logger:
    """ Create custom logger.

    :returns: Logger,
    """
    logger.remove()
    logger.add(stdout, level=LOG_LEVEL, colorize=True, format=formatter)
    logger.debug("Setup logger for logging.")
