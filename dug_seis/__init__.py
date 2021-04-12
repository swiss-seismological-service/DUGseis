#  Celery App
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
import logging
import sys

import click


###########################
## Logging Setup
class _LoggingFormatter(logging.Formatter):
    msg_map = {
        "NOTSET": click.style("NOTSET", fg="magenta", bold=True),
        "DEBUG": click.style("DEBUG", fg="green", bold=True),
        "INFO": click.style("INFO", fg="blue", bold=True),
        "WARNING": click.style("WARNING", fg="yellow", bold=True),
        "ERROR": click.style("ERROR", fg="red", bold=True),
        "CRITICAL": click.style(
            "CRITICAL", fg="white", bg="bright_red", bold=True
        ),
    }

    def format(self, record: logging.LogRecord):
        msg = self.msg_map[record.levelname]
        return (
            f"[{self.formatTime(record)}] {msg} - {record.name}: "
            f"{record.msg}"
        )

__logger = logging.getLogger(__name__)
__logger.setLevel(logging.INFO)
__ch = logging.StreamHandler(stream=sys.stdout)
__ch.setLevel(logging.INFO)


__formatter = _LoggingFormatter()
__ch.setFormatter(__formatter)

__logger.addHandler(__ch)
###########################



try:
    from celery import Celery

    celery_app = Celery(main='dug_seis')
    # Use previously generated config.
    celery_app.config_from_object('dug_seis.celeryconfig')

except ImportError:
    pass