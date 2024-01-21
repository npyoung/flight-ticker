#!/usr/bin/python
from FlightRadar24 import FlightRadar24API
from shapely.geometry import Point, Polygon
from dataclasses import dataclass
import logging
import requests
import time
import tomllib


ROI_POLYGON = Polygon(
    [
        [37.586062, -122.349855],
        [37.422485, -122.140111],
        [37.507917, -122.052749],
        [37.625808, -122.342403]
    ]
)

CENTER = Point(37.537619, -122.168786)

POLLING_INTERVAL = 5

LOCAL_URL = "http://adsbexchange.local/tar1090/data/aircraft.json"


def closest_flight():
    bbox = ROI_POLYGON.bounds
    
    response = requests.get(LOCAL_URL)
    data = response.json()
    aircraft = data['aircraft']

    closest_aircraft = None
    closest_distance = 1000

    for record in aircraft:
        if 'lat' in record and 'lon' in record and 'flight' in record:
            lat = record['lat']
            lon = record['lon']
            point = Point(lat, lon)

            if ROI_POLYGON.contains(point):
                distance = point.distance(CENTER)
                if distance < closest_distance:
                    closest_aircraft = record
                    closest_distance = distance
    
    return closest_aircraft

def get_flight_table(api, zone_name):
    zone = api.get_zones()[zone_name]
    bounds = api.get_bounds(zone)
    flights = api.get_flights(bounds=bounds)
    return {flight.callsign: flight for flight in flights}
    
def main():
    with open("config.toml", 'rb') as f:
        config = tomllib.load(f)

    fr_api = FlightRadar24API(
        user=config['flightradar24']['user'],
        password=config['flightradar24']['password']
    )

    known_flights = get_flight_table(fr_api, "northamerica")
    last_adsb_callsign = ""
    retried = False
    
    t0 = time.time() - POLLING_INTERVAL

    while True:
        t1 = time.time()

        if t1 - t0 >= POLLING_INTERVAL:
            t0 += POLLING_INTERVAL
            
            adsb_flight = closest_flight()
            if adsb_flight and adsb_flight['flight']:
                adsb_flight['flight'] = adsb_flight['flight'].strip()

                if adsb_flight['flight'] != last_adsb_callsign:
                    last_adsb_callsign = adsb_flight['flight']
                    retried = False

                if adsb_flight['flight'] not in known_flights and not retried:
                    known_flights = get_flight_table(fr_api, "northamerica")
                    retried = True
                
                if adsb_flight['flight'] in known_flights:
                    flight = known_flights[adsb_flight['flight']]
                    print(f"{flight.callsign} {flight.aircraft_code} {flight.origin_airport_iata}->{flight.destination_airport_iata}")


if __name__ == "__main__":
    main()