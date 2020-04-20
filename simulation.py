from structures import *

class Simulation(object):
    def __init__(self, airport_set='large', n_aircrafts=1000, flight_frequency = 15,
        start=default_start, end=default_end):

        random.seed('privacy')

        self.start_time=start
        self.curr_time=start
        self.end_time=end
        self.frequency=flight_frequency/60     # translate from minute to hour

        if type(airport_set) is Airports:
            self.airports=airport_set
        else:
            self.airports=airports_from_file(airport_set)

        self.aircrafts = list()
        for i in range(n_aircrafts):
            self.aircrafts.append(new_aircraft(self.airports.elements, birth=self.start_time))

    def __str__(self):
        return "My Simulation"

    def start(self):
        print("Starting simulation")
        while self.curr_time < self.end_time:

            self.get_random_on_ground(self.curr_time).new_flight(self.get_random_airport(), self.curr_time)
            self.curr_time=time_add([self.curr_time, self.frequency])
        self.end()

    def end(self):
        for a in self.aircrafts:
            a.end_sim(self.end_time)
        print("Simulation over")

    def get_random_on_ground(self, time):
        # return a random aircraft from the set that is on ground 
        a = self.aircrafts[random.randint(0, len(self.aircrafts)-1)]
        while not a.on_ground(time):
            a = self.aircrafts[random.randint(0, len(self.aircrafts)-1)]
        return a

    def get_random_airport(self):
        # return a random airport
        return self.airports.elements[random.randint(0, len(self.airports.elements)-1)]

