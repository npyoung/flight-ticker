#!/usr/bin/python
from FlightRadar24 import FlightRadar24API
from shapely.geometry import Point, Polygon
import logging
from math import radians, acos, sin, cos
from pathlib import Path
import serial
import subprocess
import time
import toml

from driver import build_output_frame, write_output_frame

ROI_POLYGON = Polygon(
    [
        [37.481003, -122.230354],
        [37.731009, -122.212237],
        [37.480771, -121.940234],
        [37.469006, -122.208103]
    ]
)

RADIUS_KM = 25
CENTER = (37.537619, -122.168786)
CENTER_POINT = Point(*CENTER)
POLLING_INTERVAL = 15
ROW_SHIFT = 0.15
LINE_TIME = 4.0
SERIAL_PORT = "/dev/ttyS0"


def flight_in_polygon(flight):
    point = Point(flight.latitude, flight.longitude)
    return ROI_POLYGON.contains(point)

def flight_distance(flight):
    lat1 = radians(flight.latitude)
    lon1 = radians(flight.longitude)
    lat2 = radians(CENTER[0])
    lon2 = radians(CENTER[1])
    return acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1)) * 6371

def main():
    config = toml.load(Path(__file__).parent / "config.toml")

    fr_api = FlightRadar24API(
        user=config['flightradar24']['user'],
        password=config['flightradar24']['password']
    )

    bounds = fr_api.get_bounds_by_point(*CENTER, RADIUS_KM * 1000)
    closest_flight = None
    t0 = time.time() - POLLING_INTERVAL

    device = serial.Serial(SERIAL_PORT, 38400)
    last_frame = build_output_frame(" ")

    while True:
        t1 = time.time()

        if t1 - t0 >= POLLING_INTERVAL:
            t0 += POLLING_INTERVAL
            flights = fr_api.get_flights(bounds=bounds)
            flights = filter(flight_in_polygon, flights)
            closest_flight = min(flights, key=flight_distance)

        if closest_flight:
            output_strings = [
                f"{closest_flight.callsign} {closest_flight.aircraft_code}",
                f"{closest_flight.origin_airport_iata}->{closest_flight.destination_airport_iata}"
            ]
            
            for s in output_strings:
                logging.info(s)
                new_frame = build_output_frame(s)
                last_frame = write_output_frame(device, new_frame, last_frame, ROW_SHIFT, 1, 0.01)
                time.sleep(LINE_TIME)
            
        else:
            logging.info("No planes found")
            new_frame = build_output_frame(s)
            last_frame = write_output_frame(device, new_frame, last_frame, ROW_SHIFT, 1, 0.01)
            time.sleep(LINE_TIME)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
