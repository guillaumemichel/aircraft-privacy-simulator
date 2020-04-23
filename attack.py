from distributions import Distribution
from structures import *
from copy import deepcopy

n_aircraft=10
airports=airports_from_file('large')
flight_frequency=timedelta(days=1)
mode='random'
policy='no_privacy' # no_privacy, 60-days, 20-days, max_privacy

def verify(flights, prediction):
    if len(flights)!=len(prediction):
        print('cannot verify! prediction and flights should have the same length')
        sys.exit(1)
    success=0
    for i in range(len(flights)):
        if flights[i].aircraft_id==prediction[i].aircraft_id:
            success+=1
    return success/len(flights)

def get_flights():
    dis = Distribution(mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency)

    flights=dis.run(timedelta(days=180))
    return flights

def get_anonymized_flights(flights):
    new_flights = deepcopy(flights)
    seen=set()
    for f in new_flights:
        if f.aircraft_id in seen:
            f.aircraft_id=None
        else:
            seen.add(f.aircraft_id)
    return new_flights

def solve_random(flights):
    for f in flights:
        f.aircraft_id=random.randint(0,n_aircraft-1)
    return flights

if __name__ == '__main__':

    flights = get_flights()
    prediction=solve_random(get_anonymized_flights(flights))
    success=verify(flights=flights, prediction=prediction)*100
    print('  %.2f%% of success' % success)
