import copy
import numpy as np
import pyproj

from dug_seis.gui.gui_util import param_yaml_to_processing
from obspy.core.event import Origin, Arrival


def locate(dug_seis_param, event):
    """
    Apply a localization algorithm that makes use of the picks
    done by the picker module.
    """
    event = event.copy()
    param = param_yaml_to_processing(dug_seis_param)

    lparam = param["Loc_Mag"]["Locate"]
    if lparam["algorithm"] == "hom_aniso":
        aparam = lparam["hom_aniso"]

    # Filter by p picks.
    event_picks = []
    for pick in event.picks:
        pick = copy.deepcopy(pick)
        if pick.phase_hint and pick.phase_hint.lower() != "p":
            continue
        event_picks.append(pick)

    # apply localization if there is a minimum number of picks
    # done for the event.
    if len(event_picks) < lparam["min_picks"]:
        print("Not enough picks.")
        return

    starttime = min([p.time for p in event_picks])

    channel_idxs = []
    # time relative to startime of snippets, in milliseconds.
    t_relative = []
    for pick in event_picks:
        # Filtering out stations where all coordinates are 0.
        # TODO  Is that necessary? And HERE?
        #       Is it meant only to filter out the first station?
        if np.max(
            np.abs(
                param["General"]["sensor_coords"][
                    int(pick.waveform_id["station_code"]) - 1, :
                ]
            )
        ):
            channel_idxs.append(int(pick.waveform_id["station_code"]) - 1)
            t_relative.append(
                (pick.time - starttime) * 1000
            )
    npicks = len(t_relative)
    sensor_coords = param["General"]["sensor_coords"][channel_idxs, :]
    vp = param["General"]["vp"] * np.ones([npicks]) / 1000.0

    if lparam["algorithm"] == "hom_iso" or lparam["algorithm"] == "hom_aniso":
        loc = sensor_coords[t_relative.index(min(t_relative)), :] + 0.1
        t0 = min(t_relative)
        nit = 0
        jacobian = np.zeros([npicks, 4])
        dm = 1.0 * np.ones(4)

        while nit < 100 and np.linalg.norm(dm) > 0.00001:
            nit = nit + 1

            # calculate anisotropic velocities
            if lparam["algorithm"] == "hom_aniso":
                for i in range(npicks):
                    azi = np.arctan2(
                        sensor_coords[i, 0] - loc[0], sensor_coords[i, 1] - loc[1]
                    )
                    inc = np.arctan2(
                        sensor_coords[i, 2] - loc[2],
                        np.linalg.norm(sensor_coords[i, range(2)] - loc[range(2)]),
                    )
                    theta = np.arccos(
                        np.cos(inc)
                        * np.cos(azi)
                        * np.cos(aparam["inc"])
                        * np.cos(aparam["azi"])
                        + np.cos(inc)
                        * np.sin(azi)
                        * np.cos(aparam["inc"])
                        * np.sin(aparam["azi"])
                        + np.sin(inc) * np.sin(aparam["inc"])
                    )
                    vp[i] = (
                        aparam["vp_min"]
                        / 1000.0
                        * (
                            1.0
                            + aparam["delta"] * np.sin(theta) ** 2 * np.cos(theta) ** 2
                            + aparam["epsilon"] * np.sin(theta) ** 4
                        )
                    )

            dist = [np.linalg.norm(loc - sensor_coords[i, :]) for i in range(npicks)]
            tcalc = [dist[i] / vp[i] + t0 for i in range(npicks)]

            res = [t_relative[i] - tcalc[i] for i in range(npicks)]
            rms = np.linalg.norm(res) / npicks
            for j in range(3):
                for i in range(npicks):
                    jacobian[i, j] = -(sensor_coords[i, j] - loc[j]) / (vp[i] * dist[i])
            jacobian[:, 3] = np.ones(npicks)

            dm = np.matmul(
                np.matmul(
                    np.linalg.inv(
                        np.matmul(np.transpose(jacobian), jacobian)
                        + pow(lparam["damping"], 2) * np.eye(4)
                    ),
                    np.transpose(jacobian),
                ),
                res,
            )
            loc = loc + dm[0:3]
            t0 = t0 + dm[3]
    else:
        print("Location algorithm not implemented. Location not estimated.")

    x = loc[0] + param["General"]["origin_ch1903_east"]
    y = loc[1] + param["General"]["origin_ch1903_north"]
    z = loc[2] + param["General"]["origin_elev"]
    t0 = starttime + t0 / 1000.0

    # convert coordinates to WGS84
    proj_ch1903 = pyproj.Proj(init="epsg:21781")
    proj_wgs84 = pyproj.Proj(init="epsg:4326")
    lon, lat = pyproj.transform(proj_ch1903, proj_wgs84, x, y)

    # create origin object and append to event
    o = Origin(
        time=t0,
        longitude=lon,
        latitude=lat,
        depth=z,
        resource_id="%s/origin/%d" % (event.resource_id.id, len(event.origins) + 1),
        depthType="elevation",
        methodID=lparam["algorithm"],
    )
    for i in event_picks:
        if param["General"]["sensor_coords"][int(i.waveform_id["station_code"]) - 1, 0]:
            o.arrivals.append(
                Arrival(
                    pick_id=i.resource_id,
                    time_residual=res[len(o.arrivals)] / 1000,
                    phase="p",
                    resource_id="%s/origin/%d/arrival/%d"
                    % (event.resource_id.id, len(event.origins) + 1, len(o.arrivals)),
                )
            )
    o.time_errors = rms / 1000
    event.origins.append(o)
    event.preferredOriginID = o.resource_id
    o.extra = {
        "x": {
            "value": loc[0],
            "namespace": "http://sccer-soe.ch/local_coordinates/1.0",
        },
        "y": {
            "value": loc[1],
            "namespace": "http://sccer-soe.ch/local_coordinates/1.0",
        },
        "z": {
            "value": loc[2],
            "namespace": "http://sccer-soe.ch/local_coordinates/1.0",
        },
    }
    print(
        "Event "
        + ": Location %3.2f %3.2f %3.2f; %i iterations, rms %4.3f ms"
        % (loc[0], loc[1], loc[2], nit, rms)
    )

    return event
