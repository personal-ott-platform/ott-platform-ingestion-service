"""
Configuration for logging in the application.
"""
import logging
import os
import sys

def setup_logging():
    """
    Configure the logging for the application.
    """
    logging.basicConfig(
        stream=sys.stdout,
        level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True,
    )
