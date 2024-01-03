#!/usr/bin/python
from shapely.geometry import Point, Polygon
import logging
import requests
import time

ROI_VERTICES = [
    [37.586062, -122.349855],
    [37.422485, -122.140111],
    [37.507917, -122.052749],
    [37.625808, -122.342403]
]

CENTER = [37.537619, -122.168786]

POLLING_INTERVAL = 60 * 60

# e.g. https://airlabs.co/api/v9/flights?api_key=32b0f92f-58ea-4dda-8231-de37ec385b59&bbox=37.428009,-122.334362,37.673579,-121.896671
ENDPOINT_URL = "https://airlabs.co/api/v9/flights"
API_KEY = "32b0f92f-58ea-4dda-8231-de37ec385b59"


def get_flight(polygon):
    bbox = polygon.bounds
    api_url = f"{ENDPOINT_URL}?api_key={API_KEY}&bbox={",".join(map(str, bbox))}"
    response = requests.get(api_url)
    data = response.json()

    in_poly = filter(lambda record: polygon.contains(Point(record['lat'], record['lng'])) and record['status'] == "en-route", data['response'])
    closest = min(in_poly, key=lambda record: (record['lat'] - CENTER[0])**2 + (record['lng'] - CENTER[1])**2)


def display_flight_info(record):
    print(f"{record['airline_iata']}{record['flight_number']} {record['aircraft_icao']} {record['dep_iata']}->{record['arr_iata']}")
    

def main():
    roi_polygon = Polygon(ROI_VERTICES)
    record = get_flight(roi_polygon)
    display_flight_info(record)
    
    t0 = time.time()

    while True:
        t1 = time.time()

        if t1 - t0 > POLLING_INTERVAL:
            t0 += POLLING_INTERVAL
            
            record = get_flight(roi_polygon)
            display_flight_info(record)


if __name__ == "__main__":
    main()