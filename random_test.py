import random
from datetime import datetime, timedelta
from structures import *

random.seed('privacy')

start = datetime.strptime('2020-01-01 12:00:00', time_format)

airports = airports_from_file('large')

fleet = list()
for i in range(10):
    callsign = 'DCM'+str(random.randint(1,9999))
    fleet.append(Aircraft(callsign=callsign, icao=get_icao(), location=airports.random()))

f0 = fleet[0].new_flight(airports.random(), start)
f1 = fleet[0].new_flight(airports.random(), time_add([start, f0.duration, 2]))

ac_test = Aircraft(callsign='TEST', icao=get_icao(), location=airports.get('KJFK'))
f_test = ac_test.new_flight(destination=airports.get('KLAX'),dep_time=start)

print(f_test)

print(f0)
print(f1)

print(get_icao())
print(get_icao())