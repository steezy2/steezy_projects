# Satellite Propagation and Collision Analysis

This project analyzes satellite propagation from 3LE data from space-track.org to warn if there is a chance of collision for in-operation satellites.

## Setup

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure the project:**

    - Open `src/config.py` and enter your space-track.org credentials (`SPACE_TRACK_USER` and `SPACE_TRACK_PASSWORD`).
    - In the same file, define the `SATELLITES_OF_INTEREST` list with the NORAD IDs of the satellites you want to track.

## Usage

To run the collision analysis, execute the `main.py` script:

```bash
python -m src.main
```

The script will fetch the latest TLE data, propagate the satellite orbits, and print any potential collisions to the console.
