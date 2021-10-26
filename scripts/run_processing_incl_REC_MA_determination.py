"""
Example processing script.
"""
import logging

import obspy
import tqdm
import numpy as np

# Import from the DUGSeis library.
from dug_seis.project.project import DUGSeisProject
from dug_seis import util

from aurem.aurem import REC

from dug_seis.event_processing.detection.dug_trigger import dug_trigger
from dug_seis.event_processing.picking.dug_picker import dug_picker
from dug_seis.event_processing.location.locate_homogeneous import (
    locate_in_homogeneous_background_medium,
)
from dug_seis.event_processing.magnitudes.amplitude_based_magnitudes import amplitude_based_relative_magnitude
from dug_seis.plotting.plotting import plot_time_waveform,\
                                        plot_time_characteristic_function,\
                                        plot_waveform_characteristic_function,\
                                        plot_waveform_characteristic_function_magnitude
from obspy.core.event import Magnitude


# The logging is optional, but useful.
util.setup_logging_to_file(
    # folder=".",
    # If folder is not specified it will not log to a file but only to stdout.
    folder=None,
    log_level="info",
)
logger = logging.getLogger(__name__)

# Load the DUGSeis project.
project = DUGSeisProject(config="run_processing_incl_REC_MA_determination.yaml")

# Helper function to compute intervals over the project.
intervals = util.compute_intervals(
    project=project, interval_length_in_seconds=5, interval_overlap_in_seconds=0.1
)

total_event_count = 0

for interval_start, interval_end in tqdm.tqdm(intervals):
    # Run the trigger only on a few waveforms.
    st_triggering = project.waveforms.get_waveforms(
        channel_ids=[
            "XB.02.01.001",
            "XB.02.03.001",
            "XB.02.10.001",
            "XB.04.01.001",
            "XB.04.02.001",
            "XB.03.12.001",
            "XB.03.15.001"],
        start_time=interval_start,
        end_time=interval_end,
    )

    # Standard DUGSeis trigger.
    detected_events = dug_trigger(
        st=st_triggering,
        # Helps with classification.
        active_triggering_channel="XB.01.01.001",
        minimum_time_between_events_in_seconds=0.015,
        max_spread_electronic_interference_in_seconds=2e-5,
        # Passed on the coincidence trigger.
        conincidence_trigger_opts={
            "trigger_type": "recstalta",
            "thr_on": 3.8,
            "thr_off": 2.0,
            "thr_coincidence_sum": 2,
            # The time windows are given in seconds.
            "sta": 1.0 / 200000.0 * 70,
            "lta": 1.0 / 200000.0 * 700,
            "trigger_off_extension": 0.01,
            "details": True,
        },
    )

    logger.info(
        f"Found {len(detected_events)} event candidates in interval "
        f"{interval_start}-{interval_end}."
    )

    if not detected_events:
        continue
    else:
        x = 2

    # Now loop over the detected events.
    added_event_count = 0
    all_channels = sorted(project.channels.keys())

    for event_candidate in detected_events:
        # Get the waveforms for the event processing. Note that this could
        # use the same channels as for the initial trigger or different ones.
        st_event = project.waveforms.get_waveforms(
            # All but the first because that is the active triggering channel
            # here.
            channel_ids=[
                "XB.02.01.001",
                "XB.02.03.001",
                "XB.02.10.001",
                "XB.04.01.001",
                "XB.04.02.001",
                "XB.03.12.001",
                "XB.03.15.001"],
            start_time=event_candidate["time"] - 5e-3,
            end_time=event_candidate["time"] + 35e-3,
        )

        # Optionally remove the instrument response if necessary.
        # Requires StationXML files where this is possible.
        # st_event.remove_response(inventory=project.inventory, output="VEL")

        st_window = 70
        lt_window = 700
        tr_on = 3.5
        tr_off = 2.0

        picks = dug_picker(
            st=st_event,
            pick_algorithm="sta_lta",
            picker_opts={
                # Here given as samples.
                "st_window": st_window,
                "lt_window": lt_window,
                "threshold_on": tr_on,
                "threshold_off": tr_off,
            },
        )

        # We want at least three picks, otherwise we don't designate it an event.
        if len(picks) < 3:
            # Optionally save the picks to the database as unassociated picks.
            # if picks:
            #    project.db.add_object(picks)
            continue

        # refine recSTA/LTA picks here
        st_event_copy = st_event.copy()
        win_pre = 0.0025
        win_post = 0.0025
        for index, pick in enumerate(picks):
            trace_1 = st_event_copy.select(id=pick.waveform_id.id)[0]
            trace_1 = trace_1.trim(starttime=pick.time - win_pre, endtime=pick.time + win_post)

            recobj = REC(trace_1)
            recobj.work()
            idx_REC = recobj.get_pick_index()
            pt = recobj.get_pick()
            # only take refined pick when delta below 0.8 * window pre STA/LTA pick
            if np.abs(picks[index].time - pt) <= 0.8 * win_pre:
                picks[index].time = pt

        # locate event
        event = locate_in_homogeneous_background_medium(
            picks=picks,
            coordinates=project.cartesian_coordinates,
            velocity=5400.0,
            damping=0.01,
            local_to_global_coordinates=project.local_to_global_coordinates)

        # get magnitude
        event = amplitude_based_relative_magnitude(st_event, event)
        event.write("out.xml", format="quakeml", validate=True)

        # plot magnitude figure
        fig = plot_waveform_characteristic_function_magnitude(st_event, st_window, lt_window, tr_on, tr_off, event)
        fig.set_size_inches(11.69, 8.27)
        fig.show()

        # exit()

        # Write the classification as a comment.
        event.comments = [
            obspy.core.event.Comment(
                text=f"Classification: {event_candidate['classification']}"
            )
        ]

        # Could optionally do a QA step here.
        if event.origins[0].time_errors.uncertainty > 5e-4:
            logger.info(
                "Rejected event. Time error too large: "
                f"{event.origins[0].time_errors.uncertainty}"
            )
            continue

        # Add the event to the project.
        event.write("out.xml", format="quakeml", validate=True)
        added_event_count += 1
        project.db.add_object(event)
    logger.info(
        f"Successfully located {added_event_count} of "
        f"{len(detected_events)} event(s)."
    )
    total_event_count += added_event_count

logger.info("DONE.")
logger.info(f"Found {total_event_count} events.")

# Possibly dump the database as a list of quakeml files.
project.db.dump_as_quakeml_files(folder="quakeml")
