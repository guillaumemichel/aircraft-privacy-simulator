from simulation import Simulation
from structures import date

if __name__ == "__main__":
    sim = Simulation()
    sim.start()

    #sim.aircrafts[9].print_flights()
    sim.airports.get('KLGA').print_aircraft_at(date("2020-04-17 16:01:05"))