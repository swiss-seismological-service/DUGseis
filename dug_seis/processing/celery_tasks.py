# helper file to collect all celery functions
# DUG-Seis ASDF converter
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

from dug_seis import celery_app
from dug_seis.processing.event_processing import event_processing
import logging
from logging.handlers import RotatingFileHandler
from celery.utils.log import get_task_logger
import celery


@celery.signals.after_setup_logger.connect
def on_after_setup_logger(**kwargs):
    logger = get_task_logger('dug-seis-events')
    logging.getLogger('matplotlib.font_manager').disabled = True
    log = 'dug-seis-events.log'
    fh = RotatingFileHandler(log)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)-7s %(message)s')
    fh.formatter = formatter
    logger.addHandler(fh)
    logger.propagate = True


@celery_app.task()
def event_processing_celery(param, snippet, event_id, classification):
    logger = get_task_logger('dug-seis-events')
    event_processing(param, snippet, event_id, classification, logger)
