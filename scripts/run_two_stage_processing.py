# flake8: noqa
"""
Example script demonstrating how a two stage processing would be run.

This is not a valid script but demonstrates the idea.
"""
import tqdm

# Import from the DUGSeis library.
from dug_seis.project.project import DUGSeisProject
from dug_seis import util


# Load project.
project = DUGSeisProject(config="dug_seis_example.yaml")


# Loop over waveforms to find picks.
intervals = util.compute_intervals(
    project=project, interval_length_in_seconds=5, interval_overlap_in_seconds=0.1
)

for interval_start, interval_end in tqdm.tqdm(intervals):
    # Run the trigger only on a few waveforms.
    st_triggering = project.waveforms.get_waveforms(
        channel_ids=[
            "GRM.001.001.001",
            "GRM.016.001.001",
            "GRM.017.001.001",
            "GRM.018.001.001",
            "GRM.019.001.001",
            "GRM.020.001.001",
        ],
        start_time=interval_start,
        end_time=interval_end,
    )

    # Call some picker.
    picks = deep_learning_picker(st, ...)

    # Add unassociated picks to the database.
    for p in picks:
        project.db.add_object(p)


# Second step: Get unassociated picks, associate and locate.
picks = project.db.get_unassociated_picks()

grouped_picks = phase_associator(picks, ...)

for pick_group in grouped_picks:
    event = event_locator(picks=pick_group, **{...})

    # Add event to database.
    project.db.add_object(event)
