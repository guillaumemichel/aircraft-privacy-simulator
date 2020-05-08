from structures import *

modes=['random']
policies=['no_privacy','60-days', '20-days', 'callsign-change', 'max_privacy']

class Distribution(object):

    # flight information accuracy (departure/arrival)
    def __init__(self, mode, policy, airports, n_aircraft, callsigns=['DCM'], \
            start_time=default_start, flight_frequency=timedelta(minutes=15), \
            n_categories=1, accuracy=1):
        random.seed('privacy')

        if mode not in modes:
            print('Invalid Distribution mode:', mode)
            print('Available modes are', modes)
            sys.exit(1)
        if policy not in policies:
            print('Invalid Distribution policy:', policy)
            print('Available modes are', policies)
            sys.exit(1)

        self.mode=mode
        self.policy=policy
        self.airports=airports.elements
        self.callsigns=callsigns
        self.start_time=start_time
        self.flight_frequency=flight_frequency
        self.categories=n_categories
        self.accuracy=accuracy

        self.assigned_callsigns=set()
        self.aircraft=list()

        if policy == policies[1]:
            self.update_freq=60
        elif policy == policies[2]:
            self.update_freq=20
        else:
            self.update_freq=None

        for i in range(n_aircraft):
            self.new_aircraft()


    def initial_next_update(self):
        if self.policy == policies[0]: # no_privacy
            return None
        if self.policy in policies[1:3]: # 20-days or 60-days
            return time_add([self.start_time, timedelta(days=random.randint(1,self.update_freq))])
        return None

    def new_callsign(self, callsign=None):
        if callsign in self.assigned_callsigns:
            self.assigned_callsigns.remove(callsign)
        callsign = callsign[:3]+str(random.randint(1,9999))
        while callsign in self.assigned_callsigns:
                callsign = callsign[:3]+str(random.randint(1,9999))
        return callsign

    def update_aircraft(self, aircraft, time):
        if self.policy in policies[-2:] or self.policy in policies[1:3] and aircraft.next_update <= time:
            aircraft.callsign = self.new_callsign(aircraft.callsign)
            if self.policy in policies[1:3] or self.policy == policies[-1]:
                aircraft.icao = get_icao(aircraft.icao)
                if self.policy!=policies[-1]: # max_privacy
                    while aircraft.next_update <= time: 
                        aircraft.next_update = time_add([aircraft.next_update, timedelta(days=self.update_freq)])
            return True
        return False

    def new_aircraft(self):
        if self.mode == modes[0]:
            # random mode
            location = self.airports[random.randint(0, len(self.airports)-1)]
            callsign = self.new_callsign(self.callsigns[random.randint(0, len(self.callsigns)-1)])
            icao = get_icao()
            next_update=self.initial_next_update()
            self.aircraft.append(Aircraft(callsign=callsign, icao=icao, location=location,\
                birth=self.start_time, next_update=next_update, cat=random.randint(0,self.categories)))

    def get_random_on_ground(self, time):
        # return a random aircraft from the set that is on ground 
        a = self.aircraft[random.randint(0, len(self.aircraft)-1)]
        c=0
        while not a.on_ground(time) and c < 1000:
            a = self.aircraft[random.randint(0, len(self.aircraft)-1)]
            c+=1
        if c>=1000:
            print('not enought aircraft, sorry')
            sys.exit(1)
        return a

    def new_flight(self, time):
        if self.mode == modes[0]:
            aircraft = self.get_random_on_ground(time)
            self.update_aircraft(aircraft=aircraft, time=time)
            destination = self.airports[random.randint(0, len(self.airports)-1)]
            return aircraft.new_flight(destination=destination, dep_time=time)

    def run(self, duration, time=None):
        if time is None:
            time=time_add([self.start_time, self.flight_frequency])

        flights=list()
        if self.mode == modes[0]:
            # random mode
            until = time_add([time, duration, self.flight_frequency])
            while time < until:
                flights.append(self.new_flight(time=time))
                time = time_add([time, self.flight_frequency])
            for a in self.aircraft:
                a.end_sim(time)

        for f in flights:
            # accuracy
            if random.uniform(0, 1)<(1-self.accuracy)/2:
                # departure is lost
                f.dep_airport=None
                f.dep_time=None
                f.duration=None
            if random.uniform(0, 1)<(1-self.accuracy)/2:
                # arrival is lost
                f.arr_airport=None
                f.arr_time=None
                f.duration=None
        return flights
                
