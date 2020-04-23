from simulation import Simulation
from distributions import Distribution
from structures import date, airports_from_file
from datetime import timedelta

if __name__ == "__main__":
    """
    sim = Simulation()
    sim.start()

    #sim.aircrafts[9].print_flights()
    sim.airports.get('KLGA').print_aircraft_at(date("2020-04-17 16:01:05"))
    """
    dis = Distribution(mode='random', policy='max_privacy', airports=airports_from_file('large'), \
        n_aircraft=1, flight_frequency=timedelta(days=1))
    flights=dis.run(timedelta(days=180))
    icao = flights[0].icao
    for f in flights:
        #if f.icao==icao:
            print(f)