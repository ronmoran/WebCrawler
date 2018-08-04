#!/usr/bin/env python3
import click
import logging
from logging import handlers
from src import TinyWriter, TorNavigator
from time import sleep


def set_logger(disk_log_path=None):
    logger = logging.getLogger("Crawler")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    if disk_log_path is None:
        return
    rotate = handlers.RotatingFileHandler(disk_log_path, maxBytes=1024*1024)
    logger.addHandler(rotate)


@click.command()
@click.option("--log-path", type=click.STRING, default=None,
              help="Path to disk log, defaults to None and doesn't write to disk")
@click.option("--sample-wait", type=click.INT, default=4,
              help="Time in hours for difference between samples. Default is 4 hours")
def main(log_path, sample_wait):
    """
    Runner of the crawler. Pass log-path if you're interesting in keeping the path, or --sample-wait to change sampling rate
    """
    set_logger(log_path)
    tor_navigator = TorNavigator()
    tiny_writer = TinyWriter()
    while True:
        new_pastes = tor_navigator.new_pastes_to_write()
        tiny_writer.write_json_entries(new_pastes)
        sleep(sample_wait * 3600)
