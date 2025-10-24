# src/collision_analysis.py

import numpy as np
from sgp4.api import Satrec
from sgp4.api import jday

def parse_3le(tle_data):
    """Parses 3LE data into a list of Satrec objects."""
    lines = tle_data.strip().split('\r\n')
    satellites = []
    for i in range(0, len(lines), 3):
        line0 = lines[i].strip()
        line1 = lines[i+1].strip()
        line2 = lines[i+2].strip()
        satellite = Satrec.twoline2rv(line1, line2)
        satellite.name = line0
        satellites.append(satellite)
    return satellites

def propagate_satellites(satellites, start_time, end_time, time_step):
    """Propagates a list of satellites over a given time period."""
    propagated_positions = []
    for satellite in satellites:
        positions = []
        jd = start_time
        while jd <= end_time:
            error, r, v = satellite.sgp4(jd, 0)
            if error == 0:
                positions.append(r)
            else:
                positions.append(None) # Error in propagation
            jd += time_step
        propagated_positions.append(positions)
    return propagated_positions

def check_collisions(propagated_positions, threshold):
    """Checks for collisions between propagated satellite positions."""
    num_satellites = len(propagated_positions)
    num_time_steps = len(propagated_positions[0])
    collisions = []

    for i in range(num_satellites):
        for j in range(i + 1, num_satellites):
            for t in range(num_time_steps):
                pos1 = propagated_positions[i][t]
                pos2 = propagated_positions[j][t]

                if pos1 is not None and pos2 is not None:
                    distance = np.linalg.norm(np.array(pos1) - np.array(pos2))
                    if distance < threshold:
                        collisions.append({
                            "sat1": i,
                            "sat2": j,
                            "time_step": t,
                            "distance": distance
                        })
    return collisions
