from dug_seis.project.project import DUGSeisProject

folder = "/home/user/VALTER_EXPERIMENT/INTERVAL7/CODES/"
project = DUGSeisProject(config=folder + "post_processing_VALTERStimu1_smallWin.yaml")


##########################
# get information from event and channels with picks
##########################

# read project database
database = project.db
# get events from the database
if True:
    events = database.get_objects(object_type="Event")

    origin_time = []
    pick_ch = []
    ev_lat = []
    ev_lon = []
    ev_depth = []

    # get picks, location and origin time from events -> structure like obspy events

    for ev in events:
        evpick = []
        ch = []
        for pick in ev.picks:
            utc = ev.origins[0].time
            evpick.append(utc.datetime)
            ch.append(pick.waveform_id.station_code)

        origin_time.append(evpick)
        pick_ch.append(ch)
        ev_lat.append(ev.origins[0].latitude)
        ev_lon.append(ev.origins[0].longitude)
        ev_depth.append(ev.origins[0].depth)

# get unassociated events from the database
unas_picks = []
unas_picks_ch = []
unas_picks_phase = []
u_picks = database.get_unassociated_picks()
for u_pick in u_picks:
    utc = u_pick.time
    unas_picks.append(utc.datetime)
    unas_picks_ch.append(
        u_pick.waveform_id.station_code
    )  # or network_code, channel_code, location_code
    unas_picks_phase.append(u_pick.phase_hint)
