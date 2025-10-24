# config.py

# Space-Track.org credentials
SPACE_TRACK_USER = "your_email@example.com"
SPACE_TRACK_PASSWORD = "your_password"

# URL for space-track.org TLE query
SPACE_TRACK_URL = "https://www.space-track.org"

# Satellites of interest (NORAD IDs)
SATELLITES_OF_INTEREST = [
    # Example: Starlink satellites
    # You can get these from celestrak.com or space-track.org
]

# Time parameters for propagation (in days)
PROPAGATION_TIME = 1  # Propagate for 1 day

# Collision threshold (in km)
COLLISION_THRESHOLD = 1.0
