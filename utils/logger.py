import logging

def setup_logger():
    """
    Sets up the logger configuration with a log file, logging level, and format.

    Returns:
        Logger: Configured logger instance.
    """
    logging.basicConfig(
        filename='app.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s'
    )

    # Ignore some debug logs that contain private information (API Key)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logging.getLogger()