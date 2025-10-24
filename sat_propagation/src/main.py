# src/main.py

from datetime import datetime, timedelta
from sgp4.api import jday
from src.config import SATELLITES_OF_INTEREST, PROPAGATION_TIME, COLLISION_THRESHOLD
from src.spacetrack_fetcher import get_spacetrack_data
from src.collision_analysis import parse_3le, propagate_satellites, check_collisions

def main():
    """Main function to run the collision analysis."""
    if not SATELLITES_OF_INTEREST:
        print("No satellites of interest defined in src/config.py")
        return

    print("Fetching TLE data from space-track.org...")
    try:
        tle_data = get_spacetrack_data(SATELLITES_OF_INTEREST)
    except Exception as e:
        print(f"Error fetching TLE data: {e}")
        return

    print("Parsing TLE data...")
    satellites = parse_3le(tle_data)

    print("Propagating satellite orbits...")
    now = datetime.utcnow()
    start_time = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
    end_time = start_time + PROPAGATION_TIME
    time_step = 1.0 / (24.0 * 60.0)  # 1 minute time step

    propagated_positions = propagate_satellites(satellites, start_time, end_time, time_step)

    print("Checking for potential collisions...")
    collisions = check_collisions(propagated_positions, COLLISION_THRESHOLD)

    if collisions:
        print("\nPotential collisions detected:")
        for collision in collisions:
            sat1_name = satellites[collision["sat1"]].name
            sat2_name = satellites[collision["sat2"]].name
            time_of_collision = now + timedelta(minutes=collision["time_step"])
            distance = collision["distance"]
            print(
                f"  - Satellites: {sat1_name} and {sat2_name}\
"  # Corrected newline escape
                f"    Time: {time_of_collision.isoformat()}\
"  # Corrected newline escape
                f"    Distance: {distance:.2f} km"
            )
    else:
        print("\nNo potential collisions detected.")

if __name__ == "__main__":
    main()
