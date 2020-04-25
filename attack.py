from distributions import Distribution
from structures import *
from copy import deepcopy

sys.setrecursionlimit(10000)

n_aircraft=100 # 1062 available icaos in total
airports=airports_from_file('medium').first(1000)
flight_frequency=timedelta(minutes=15)
mode='random'
policy='60-days' # no_privacy, callsign-change, 60-days, 20-days, max_privacy
simlength=timedelta(days=90)


def verify(flights, prediction):
    if len(flights)!=len(prediction):
        print('cannot verify! prediction and flights should have the same length')
        sys.exit(1)
    # verify correct sequence

    flights_ids=dict()
    flights_dict=dict()
    predict_ids=dict()
    predict_dict=dict()
    for i in range(len(flights)):
        flights_ids[flights[i].id]=flights[i].aircraft_id
        predict_ids[prediction[i].id]=prediction[i].aircraft_id

        if flights[i].aircraft_id not in flights_dict:
            flights_dict[flights[i].aircraft_id]=list()
        flights_dict[flights[i].aircraft_id].append((flights[i].id, flights[i].icao))
        if prediction[i].aircraft_id not in predict_dict:
            predict_dict[prediction[i].aircraft_id]=list()
        predict_dict[prediction[i].aircraft_id].append(prediction[i].id)

    score=0
    total=0
    for aircraft in flights_dict:
        my_flights=flights_dict[aircraft]
        if len(my_flights)>1:
            for i in range(1, len(my_flights)):
                if my_flights[i-1][1] != my_flights[i][1]: # icao change
                    total+=1
                    # check if both flights are in the same list
                    o = predict_dict[predict_ids[my_flights[i-1][0]]]
                    if my_flights[i][0] in o:
                        score += 1
    if total==0:
        return 1
    print(total)
    return score/total
        

    """
    success=0
    for i in range(len(flights)):
        if flights[i].aircraft_id==prediction[i].aircraft_id:
            success+=1
    return success/len(flights)
    """

def get_flights():
    dis = Distribution(mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency)

    aircraft = deepcopy(dis.aircraft)
    flights=dis.run(simlength)
    return aircraft, flights

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

def solve_no_privacy(flights):
    icaos=dict()
    for f in flights:
        if f.icao not in icaos and f.aircraft_id is not None:
            icaos[f.icao]=f.aircraft_id
        elif f.icao in icaos:
            f.aircraft_id=icaos[f.icao]
        else:
            f.aircraft_id=random.choice(list(icaos.keys()))
    return flights

def solve_callsign_change(flights):
    return solve_no_privacy(flights)

def solve_simple_location(flights):
    ids=dict() # icao -> id
    ids[flights[0].icao]=len(ids)
    for f in flights[1:]:
        #print('ids:', ids)
        check_time=time_add([f.dep_time, timedelta(milliseconds=-1)])
        old_icaos=[a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time)]
        if f.icao not in ids:
            ids[f.icao]=len(ids)
        if f.icao not in old_icaos: # change detected
            #print(f.id, f.dep_airport.icao, old_icaos, check_time)
            selected=random.choice(old_icaos) # select randomly icao
            if selected not in ids:
                ids[selected]=len(ids) # associate an aircraft id to that icao
            f.aircraft_id=ids[selected]

            ids[f.icao]=ids[selected] # update aircraft_id - icao record
            del ids[selected]
        else:
            f.aircraft_id=ids[f.icao]
    return flights

# not really working
# in case: ac0 doesn't change icao, later ac1 change icao to the one used by ac0 at the given airport
def solve_location_future(flights, aircraft):
    ids=dict() # icao -> id
    #for a in aircraft:
    #    ids[a.icao]=a.id
    #ids[flights[0].icao]=len(ids)
    for i in range(len(flights)):
        f=flights[i]
        #if f.aircraft_id is not None:
        #    ids[f.icao]=f.aircraft_id
        #    continue
        check_time=time_add([f.dep_time, timedelta(milliseconds=-1)])
        old_icaos=[a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time)]
        if f.icao not in ids:
            ids[f.icao]=len(ids)
        if len(old_icaos)>0 and f.icao not in old_icaos: # change detected
            #print(' '*50+str(old_icaos)+' '*50, end='\r')
            for j in range(i, len(flights)):
                if len(old_icaos)<=1:
                    break
                f2=flights[j]
                if f2.dep_airport==f.dep_airport and f2.icao in old_icaos:
                    ok=True
                    for f3 in flights[i:j]:
                        if f2.icao==f3.icao and f3.arr_airport==f2.dep_airport:
                            ok=False
                    if ok:
                        old_icaos.remove(f2.icao)
            #print(f.id, f.dep_airport.icao, old_icaos, check_time)
            selected=random.choice(old_icaos) # select randomly icao
            #print('selected '+selected+' among '+str(old_icaos))
            #print('ids', ids)
            if selected not in ids:
                ids[selected]=len(ids) # associate an aircraft id to that icao
            f.aircraft_id=ids[selected]

            ids[f.icao]=ids[selected] # update aircraft_id - icao record
            del ids[selected]
        else:
            if f.icao not in ids:
                ids[f.icao]=len(ids)
            f.aircraft_id=ids[f.icao]
    return flights

def get_seq(low, high, mod):
    if low <= high:
        seq=set(range(low, high+1))
    else:
        seq=set(range(low, mod+1))
        seq.update(set(range(0,high+1)))
    return seq

# only works when starting sim on Jan01
def solve_date_change(flights):
    if policy not in ['20-days', '60-days']:
        print('solve_date_change() not applicable on policy '+policy)
        return
    mod = int(policy[:2])
    ids=dict() # icao -> id
    for i in range(len(flights)):
        f=flights[i]
        check_time=time_add([f.dep_time, timedelta(milliseconds=-1)])
        old_icaos=[a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time)]
        if len(old_icaos)>0 and f.icao not in old_icaos: # change detected
            backup=deepcopy(old_icaos)

            trial=list()
            for icao in old_icaos:
                arrival=0
                for j in range(i-i, 0, -1):
                    if flights[j].icao==icao:
                        arrival=flights[j].arr_time.timetuple().tm_yday
                departure=f.dep_time.timetuple().tm_yday
                if arrival<departure-mod:
                    arrival=departure+1
                departure = departure % mod
                arrival = arrival % mod
                seq=get_seq(arrival, departure, mod)
                if icao not in ids or ids[icao][1] is None or len(ids[icao][1]&seq)>0:
                    trial.append(icao)
                else:
                    print('excluded')

            #old_icaos=trial
            unlucky=False
            for j in range(i, len(flights)):
                if len(old_icaos)<=1:
                    unlucky=True
                    break
                f2=flights[j]
                if f2.dep_airport==f.dep_airport and f2.icao in old_icaos and f2.dep_time <= time_add([f.dep_time, timedelta(days=mod)]):
                    ok=True
                    for f3 in flights[i:j]:
                        if f2.icao==f3.icao and f3.arr_airport==f2.dep_airport:
                            ok=False
                    if ok:
                        old_icaos.remove(f2.icao)

            selected=random.choice(old_icaos) # select randomly icao
            if selected not in ids:
                unlucky=True
                ids[selected]=[len(ids), None] # associate an aircraft id to that icao

            #time attack
            if len(old_icaos)==1 and not unlucky: # we're almost sure of the change
                low=0
                for j in range(i-1,0,-1):
                    if flights[j].icao==selected: # arrival of aircraft at airport
                        low=flights[j].arr_time.timetuple().tm_yday
                        break
                high=f.dep_time.timetuple().tm_yday
                if low<high-mod:
                    low=high+1
                low = low % mod
                high = high % mod

                # define seq
                seq=get_seq(low,high,mod)

                if ids[selected][1] is None:
                    ids[selected][1]=seq
                else: # intersection
                    ids[selected][1]&=seq

            f.aircraft_id=ids[selected][0]

            if unlucky:
                ids[f.icao]=[ids[selected][0],None]
            else:
                ids[f.icao]=ids[selected] # update aircraft_id - icao record
            del ids[selected]
        else:
            if f.icao not in ids:
                ids[f.icao]=[len(ids), None]
            f.aircraft_id=ids[f.icao][0]
    print(ids)
    return flights


def print_flights(flights):
    for f in flights:
        print(f)

def debug():
    dis = Distribution(mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency)

    flights=dis.run(simlength)
    f=flights[3776]
    print(f)
    print()

    check_time=time_add([f.dep_time, timedelta(milliseconds=-1)])
    string=''
    for a in f.dep_airport.aircraft_at(check_time):
        string += a.icao_at(check_time)+' '
    print(string)

    print(f.dep_airport.aircraft_at(check_time)[0])

    for h in f.dep_airport.aircraft_history:
        print(h)

    for a in dis.aircraft:
        if a.id==f.aircraft_id:
            ac=a
            break
    ac.print_flights()

if __name__ == '__main__':
    # take a list of initial aircraft with icaos from get_flights() to use in attacks
    #debug()
    
    #"""
    aircraft, flights = get_flights()
    
    #print_flights(flights)

    prediction=solve_date_change(get_anonymized_flights(flights))
    success=verify(flights=flights, prediction=prediction)*100
    print('  %.2f%% of success' % success)

    prediction=solve_location_future(get_anonymized_flights(flights),aircraft)
    #print_flights(prediction)
    
    #prediction=solve_no_privacy(get_anonymized_flights(flights))
    success=verify(flights=flights, prediction=prediction)*100
    print('  %.2f%% of success' % success)
    #"""