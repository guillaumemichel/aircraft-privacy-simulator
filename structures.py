from itertools import count
from geopy.distance import geodesic
from datetime import timedelta, datetime
import json
import sys
import random

time_format = '%Y-%m-%d %H:%M:%S'
default_start = datetime.strptime('2020-01-01 00:00:00', time_format)
default_end = datetime.strptime('2020-06-30 23:59:59', time_format)
myicaos = list()
avail_icaos = list()

class Flight(object):
    _ids = count(0)

    def __init__(self, aircraft, destination, dep_time, category): # max_velocity ?

        self.id = next(self._ids)               # flight id, unique identifier
        self.aircraft_id = aircraft.id          # aircraft id
        self.callsign = aircraft.callsign       # flight callsign
        self.icao = aircraft.icao               # flight icao
        self.aircraft_cat=category              # aircraft type
        self.dep_airport = aircraft.location    # departure airport icao address
        self.arr_airport = destination          # arrival airport icao address
        self.dep_time = dep_time                # departure time
        self.distance = float(self.dep_airport.distance(self.arr_airport)) # distance between departure and arrival airports

        if aircraft.location==destination:
            self.duration=timedelta(hours=0.5).days/24
        else:
            self.duration = float(self.distance / aircraft.avg_speed)      # flight duration in hours
        self.arr_time = time_add([self.dep_time, self.duration])

    def __str__(self):
        tostr = "Flight n°"+str(self.id)+"\n"
        tostr += "Aircraft ID:       "+str(self.aircraft_id)+"\n"
        tostr += "Callsign:          "+str(self.callsign)+"\n"
        tostr += "ICAO:              "+str(self.icao)+"\n"
        tostr += "From:              "+str(self.dep_airport.icao)+"\n"
        tostr += "To:                "+str(self.arr_airport.icao)+"\n"
        tostr += "Distance:          %.2f km\n" % self.distance
        tostr += "Departure:         "+str(self.dep_time)+"\n"
        tostr += "Arrival:           "+str(self.arr_time)+"\n"
        tostr += "Duration:          %.2f h\n" % self.duration
        return tostr

    def aircraft_string(self):
        string = " Callsign:"+' '*(14-len(self.callsign))+self.callsign+' '*5+"ICAO:   "+self.icao+"\n"
        string += " Departure:"+' '*(13-len(self.dep_airport.icao))+self.dep_airport.icao+' '*5+str(self.dep_time)+"\n"
        string += " Arrival:"+' '*(15-len(self.arr_airport.icao))+self.arr_airport.icao+' '*5+str(self.arr_time)+"\n"
        return string

class Aircraft(object):
    _ids = count(0)
    def __init__(self, callsign, icao, location, birth=default_start, \
        avg_speed=660, next_update=None, cat=0): # max_velocity
        self.id = next(self._ids)       # global aircraft id, unmutable
        self.callsign = callsign        # callsign currently assigned to aircraft
        self.icao = icao                # icao currently assigned to aircraft
        self.location = location        # current aircraft location (airport or 'flying')
        self.avg_speed = avg_speed      # average speed in km/h of the aircraft (constant for now)
        self.cat=cat                    # aircraft category
        self.history = list()           # history of flights and groundings
        self.flights = list()
        self.birth=birth
        self.next_update=next_update
        self.initial_icao=icao
        self.initial_callsign=callsign
        location.aircraft_arrival(self, self.birth)

    def __str__(self):
        tostr = "Aircraft n°"+str(self.id)+"\n"
        tostr += "Current callsign:  "+str(self.callsign)+"\n"
        tostr += "Current ICAO:      "+str(self.icao)+"\n"
        tostr += "Current location:  "+str(self.location.icao)+"\n"
        tostr += "Average Speed:     "+str(self.avg_speed)+"\n"
        tostr += "Number of flights: "+str(len(self.flights))+"\n"
        tostr += "Category:          "+str(self.cat)+"\n"
        return tostr

    def new_flight(self, destination, dep_time):
        # create a new flight for the given aircraft from its current location
        f = Flight(aircraft=self, destination=destination, dep_time=dep_time, category=self.cat)

        # append past period and flight to history
        if len(self.flights)==0:
            from_time=self.birth
        else:
            from_time=self.flights[-1].arr_time
        self.history.append(AircraftHistoryRecord(status="ground", from_time=from_time, until_time=dep_time, airport=self.location))
        self.history.append(AircraftHistoryRecord(status="flying", flight=f))
        self.flights.append(f)

        # update aircraft and airport
        self.location.aircraft_departure(self, dep_time)
        self.location = destination
        self.location.aircraft_arrival(self, f.arr_time)
        return f

    def end_sim(self, time):
        if len(self.flights)==0:
                from_time=self.birth
        else:
            from_time=self.flights[-1].arr_time
        self.history.append(AircraftHistoryRecord(status="ground", from_time=from_time, until_time=time, airport=self.location))
        self.location.aircraft_departure(self, time)


    def on_ground(self, time):
        # return true if aircraft on ground at the given time
        for h in self.history:
            if h.from_time < time < h.until_time:
                return h.status=="ground"
        return True

    def print_flights(self):
        string = 'Aircraft n°'+str(self.id)+'\n'
        string += str(len(self.flights))+' flights\n'
        for f in self.flights:
            string += f.aircraft_string()+'\n'
        print(string[:-1])

    def icao_at(self, time):
        if len(self.flights)==0:
            return None
        tmp=None
        for f in self.flights:
            if f.dep_time > time:
                break
            tmp=f
        if tmp is None:
            return self.initial_icao
        return tmp.icao

def new_aircraft(airports, birth=default_start, callsign='DCM', icao=None, avg_speed=660):
    # returns a new aircraft, with random airport, icao, callsign etc.
    location = airports[random.randint(0, len(airports)-1)]
    if len(callsign)==3:
        callsign += str(random.randint(1,9999))
    if icao is None:
        icao = get_icao()
    a = Aircraft(callsign=callsign, icao=icao, location=location, birth=birth, avg_speed=avg_speed)
    return a

class AircraftHistoryRecord(object):
    def __init__(self, status, flight=None, from_time=None, until_time=None, airport=None):
        self.status=status
        if self.status == 'flying':
            self.flight=flight
            self.from_time=flight.dep_time
            self.until_time=flight.arr_time
        elif self.status == 'ground':
            self.from_time=from_time
            self.until_time=until_time
            self.aiport=airport

class Airport(object):

    def __init__(self, icao, lat, lon, alt, cat, name):
        self.icao=icao                  # unique identifier of an airport
        self.name=name                  # airport full name
        self.lat=lat                    # airport latitude
        self.lon=lon                    # airport longitude
        self.alt=alt                    # airport altitude
        self.cat=cat                    # airport category (small/medium/large)
        self.aircraft_history=list()    # history of aircrafts that stayed at airport
        self.current_aircraft=dict()    # list of aircraft currently at airport

    def __str__(self):
        tostr = "Airport: "+str(self.icao)+"\n"
        tostr += "Fullname:          "+str(self.name)+"\n"
        tostr += "Lat/Lon/Alt:       %.4f/%.4f/%.0f\n" % (self.lat, self.lon, self.alt)#+str(self.lat)+"/"+str(self.lon)+"/"+str(self.alt)+"\n"
        tostr += "Category:          "+str(self.cat)+"\n"
        return tostr

    def distance(self, other):
        # compute distance between self and another given airport
        return geodesic((self.lat, self.lon), (other.lat, other.lon)).km

    def aircraft_arrival(self, aircraft, time):
        # add the given aircraft to the list of current aircrafts
        self.current_aircraft[aircraft.id]=(time, aircraft.callsign, aircraft.icao)

    def aircraft_departure(self, aircraft, time):
        # aircraft leaving airport, add its presence to history
        self.aircraft_history.append( \
            AirportHistoryElement(aircraft, self.current_aircraft[aircraft.id], time))
        del self.current_aircraft[aircraft.id]

    def aircraft_at(self, time):
        ac_list=list()
        for h in self.aircraft_history:
            if h.arrival_time <= time < h.departure_time:
                ac_list.append(h.aircraft)
        if len(ac_list)==0:
            print('strange: no aircraft at '+self.icao+' at '+str(time))
        return ac_list

    def print_aircraft_at(self, time):
        string = "All aircraft in "+self.icao+" at "+str(time)+'\n'
        for a in sorted(self.aircraft_at(time),key=lambda aircraft: aircraft.id):
            string += ' n°'+str(a.id)+'\n'
        print(string[:-1])

class AirportHistoryElement(object):
    def __init__(self, aircraft, record, departure_time):
        self.aircraft=aircraft
        self.arrival_time=record[0]
        self.departure_time=departure_time
        self.arr_callsign=record[1]
        self.arr_icao=record[2]
        self.dep_callsign=aircraft.callsign
        self.dep_icao=aircraft.icao
    
    def __str__(self):
        return str(self.aircraft.id)+' '+str(self.arrival_time)+'-'+str(self.departure_time)+' '+self.arr_callsign+'-'+self.dep_callsign+' '+self.arr_icao+'-'+self.dep_icao

class Airports(object):
    def emtpy(self):
        self.elements=list()

    def __init__(self):
        self.emtpy()

    def __str__(self):
        tostr = ""
        for a in self.elements:
            tostr+=str(a)
        return tostr

    def first(self, n):
        self.elements=self.elements[:n]
        return self

    def append(self, el):
        self.elements.append(el)

    def remove(self, el):
        self.elements.remove(el)

    def random(self):
        return self.elements[random.randint(0, len(self.elements)-1)]

    def get(self, icao):
        for a in self.elements:
            if a.icao == icao:
                return a
        return None

    def to_file(self, filename):
        json = '[\n'
        for a in self.elements:
            json += '  {\n'
            json += '    "icao" : "%s",\n' % a.icao
            json += '    "name" : "%s",\n' % a.name
            json += '    "lat"  : "%s",\n' % a.lat
            json += '    "lon"  : "%s",\n' % a.lon
            json += '    "alt"  : "%s",\n' % a.alt
            json += '    "cat"  : "%s"\n'  % a.cat
            json += '  },\n'
        json = json[:-2]+'\n]'

        file = open(filename, "w")
        file.write(json)
        file.close()

    def from_file(self, filename):
        file = open(filename, "r")
        data = file.read()
        file.close()

        json_data = json.loads(data)
        self.elements = list()
        for d in json_data:
            self.append(Airport(d['icao'],float(d['lat']),float(d['lon']),float(d['alt']),d['cat'],d['name']))

categories = ['large', 'medium', 'small', 'all']

def from_opensky(airport):
    # from an opensky format airport, return an Airport
    typ = 'oops'
    for c in categories[:-1]:
        if c in airport[7]:
            typ = c[0].upper()
            break
    return Airport(airport[2], airport[3], airport[4], airport[6], typ, airport[0])

def airports_from_file(category):
    # returns the airports from the given category stored in data/
    airports = Airports()
    airports.from_file('data/'+category+'_airports.json')
    return airports

def time_add(times):
    for i in range(len(times)):
        if type(times[i]) == str:
            times[i] = datetime.strptime(times[i], time_format)
        elif type(times[i]) in [int, float]:
            times[i] = timedelta(hours=times[i])

        if i == 0:
            new_time = times[i]
        else:
            new_time += times[i]
    #return new_time.strftime(time_format)
    new_time = new_time - timedelta(microseconds=new_time.microsecond)
    return new_time

def load_icaos(n=0):
    # load PIA icaos from file
    if len(myicaos)==0:
        if n==0:
            f = open('data/icaos.txt', 'r')
            myicaos.extend(f.read().split('\n')[:-1])
            f.close()
        else:
            myicaos.extend(list(range(0,n)))
        avail_icaos.extend(myicaos)

    return avail_icaos

def get_icao(old=None):
    # returns a random unused ICAO address
    if len(myicaos)==0:
        load_icaos(n=100000)
    # put back the old icao to the set
    if old is not None:
        avail_icaos.append(old)
    icao = avail_icaos[random.randint(0,len(avail_icaos)-1)]
    avail_icaos.remove(icao)
    return icao

def date(string):
    return datetime.strptime(string, time_format)
