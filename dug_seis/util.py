# DUGSeis
# Copyright (C) 2021 DUGSeis Authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Utility functionality useful across DUGSeis.
"""

import copy
import datetime
import logging
import pathlib
import typing

import obspy
import schema
import tqdm


class _TqdmLoggingHandler(logging.StreamHandler):
    """
    Avoid tqdm progress bar interruption by logger's output to console

    From https://stackoverflow.com/a/67257516
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg, end=self.terminator)
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def setup_logging_to_file(
    folder: typing.Optional[typing.Union[pathlib.Path, str]] = None,
    log_level: str = "info",
):
    """
    Helper function to setup the logging in a tqdm aware fashion.

    Args:
        folder: Folder where the log file should be stored. If not given it will
            only log to stdout.
        log_level: Desired log level as a string.
    """

    # Root logger.
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())

    # Custom formatter.
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")

    # tqdm aware log handler.
    ch = _TqdmLoggingHandler()
    ch.setLevel(log_level.upper())
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Also log to file if desired.
    if folder:
        folder = pathlib.Path(folder)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fh = logging.handlers.RotatingFileHandler(folder / f"dug-seis_{now}.log")
        fh.setLevel(log_level.upper())
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.info("=" * 60)
    logger.info("=" * 60)
    logger.info("Starting DUGSeis Logging")
    logger.info("=" * 60)
    logger.info("=" * 60)


def pretty_filesize(num: typing.Union[int, float]) -> str:
    """
    Handy formatting for human readable filesizes.

    From http://stackoverflow.com/a/1094933/1657047

    Args:
        num: The filesize in bytes.
    """
    for x in ["bytes", "KB", "MB", "GB"]:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, "TB")


def filter_settings_to_function(
    filter_settings: typing.Dict[str, typing.Any]
) -> typing.Callable:
    """
    Convert project filter settings to a callable function.

    Args:
        filter_settings: The filter settings as given in a DUGSeis project.

    Returns:
        A function that can be applied to `obspy.Trace` objects.
    """
    from dug_seis.project.project import _CONFIG_FILE_SCHEMA

    # Reuse the project schema to validate..
    filter_settings = schema.Schema(
        _CONFIG_FILE_SCHEMA.schema["filters"][0]["filter_settings"]
    ).validate(filter_settings)

    filter_types = [
        "butterworth_bandpass",
        "butterworth_highpass",
        "butterworth_lowpass",
    ]

    if filter_settings["filter_type"] not in filter_types:
        raise ValueError(
            f"Invalid filter type '{filter_settings['filter_type']}'. "
            f"Available filter types: {filter_types}"
        )

    def f(tr: obspy.Trace):
        if filter_settings["filter_type"] == "butterworth_bandpass":
            tr.filter(
                "bandpass",
                freqmin=filter_settings["highpass_frequency_in_hz"],
                freqmax=filter_settings["lowpass_frequency_in_hz"],
                corners=filter_settings["filter_corners"],
                zerophase=filter_settings["zerophase"],
            )
        elif filter_settings["filter_type"] == "butterworth_highpass":
            tr.filter(
                "highpass",
                freq=filter_settings["frequency_in_hz"],
                corners=filter_settings["filter_corners"],
                zerophase=filter_settings["zerophase"],
            )
        elif filter_settings["filter_type"] == "butterworth_lowpass":
            tr.filter(
                "lowpass",
                freq=filter_settings["frequency_in_hz"],
                corners=filter_settings["filter_corners"],
                zerophase=filter_settings["zerophase"],
            )
        else:
            raise NotImplementedError

        return tr

    return f


def compute_intervals(
    project: "dug_seis.project.project.DUGSeisProject",  # noqa
    interval_length_in_seconds: float,
    interval_overlap_in_seconds: float,
) -> typing.List[typing.Tuple[obspy.UTCDateTime, obspy.UTCDateTime]]:
    """
    Compute intervals to loop over all data in a project.

    Args:
        project: DUGSeis project object. The temporal bounds will be read from
            it.
        interval_length_in_seconds: The length of each interval in seconds.
        interval_overlap_in_seconds: The overlap between two intervals in
            seconds.

    Returns:
        A list of (start time, end time) `obspy.UTCDateTime` tuples.
    """
    start_time = project.config["temporal_range"]["start_time"]
    end_time = project.config["temporal_range"]["end_time"]

    # Just make all of them - cannot be that many and each in the end is a fancy
    # float.
    intervals = []
    interval_start = copy.deepcopy(start_time)
    while interval_start < end_time:
        interval_end = interval_start + interval_length_in_seconds
        # Nothing to do if not covered by the data.
        if (
            interval_start > project.waveforms.endtime
            or interval_end < project.waveforms.starttime
        ):
            interval_start = interval_end - interval_overlap_in_seconds
            continue
        intervals.append([interval_start, interval_end])
        # Prep for next iteration.
        interval_start = interval_end - interval_overlap_in_seconds

    return intervals
