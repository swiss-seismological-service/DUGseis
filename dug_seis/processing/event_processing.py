# Processing module of DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#

import os
import pathlib

from obspy import read
from obspy.core.event.base import Comment

from dug_seis import util
from dug_seis.processing.event import Event


def event_processing(param, wf_stream, event_id, classification, logger):
    """
    Serialize the processed events.
    """
    processing_folder = pathlib.Path(param["General"]["processing_folder"])
    quakeml_folder = processing_folder / "quakeml"
    quakeml_folder.mkdir(exist_ok=True, parents=True)

    # which modules in the event class script and the order of them to be
    # applied on the waveform can be specified here by changing the order
    # of the event modules or commenting them.
    event = Event(param, wf_stream, event_id, classification, logger)

    event.pick()
    event.locate()

    assert classification in [
        "passive",
        "active",
        "electronic",
    ], f"Unknown classification '{classification}'"

    # Write the classification as a comment.
    event.comments = [Comment(text=f"Classification: {classification}")]

    # Write the QuakeML file.
    event.write(
        str(quakeml_folder / f"event{event_id}.xml"),
        "quakeml",
        validate=True,
    )

    logger.info("Finished event processing for event %d" % event_id)
