from config import LOG_LEVEL
from sys import stdout
from loguru import logger as log


def formatter(log: dict) -> str:
    """
    Format log colors based on level.
    :param dict log: Dictionary containing log level, details, etc.
    :returns: str
    """
    if log["level"].name == "INFO":
        return (
            "<fg #aad1f7>{time:HH:mm:ss A}</fg #aad1f7> | "
            "<fg #cfe2f3>{level}</fg #cfe2f3>: "
            "<light-white>{message}</light-white> \n"
        )
    if log["level"].name == "SUCCESS":
        return (
            "<fg #aad1f7>{time:HH:mm:ss A}</fg #aad1f7> | "
            "<fg #8aa88a>{level}</fg #8aa88a>: "
            "<light-white>{message}</light-white> \n"
        )
    if log["level"].name == "WARNING":
        return (
            "<fg #aad1f7>{time:HH:mm:ss A}</fg #aad1f7> | "
            "<fg #ffe900>{level}</fg #ffe900>: "
            "<light-white>{message}</light-white> \n"
        )
    elif log["level"].name == "ERROR":
        return (
            "<fg #aad1f7>{time:HH:mm:ss A}</fg #aad1f7> | "
            "<fg #9e5757>{level}</fg #9e5757>: "
            "<light-white>{message}</light-white> \n"
        )
    else:
        return (
            "<fg #aad1f7>{time:HH:mm:ss A}</fg #aad1f7> | "
            "<fg #67c9c4>{level}</fg #67c9c4>: "
            "<light-white>{message}</light-white> \n"
        )


def configure_logger() -> log:
    """
    Create custom logger.
    :returns: custom_logger
    """
    log.remove()
    log.add(stdout, level = LOG_LEVEL, colorize = True, format = formatter)
