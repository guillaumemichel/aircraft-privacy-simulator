from distributions import Distribution
from structures import *
from copy import deepcopy
from matplotlib import pyplot as plt

sys.setrecursionlimit(10000)

intervals=30 # in minutes
searchWindow=30*24*60/intervals

n_aircraft=1000 # 1062 available icaos in total or parameter range in structures.py
airports=airports_from_file('large').first(100)
flight_frequency=timedelta(minutes=intervals)
n_categories=10
mode='random'
policy='20-days' # no_privacy, callsign-change, 60-days, 20-days, max_privacy
simlength=timedelta(days=365)


debug=False

def get_flights():
    dis = Distribution(mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency, n_categories=n_categories)

    return dis.run(simlength)

def get_anonymized_flights(flights):
    new_flights = deepcopy(flights)
    seen=set()
    for f in new_flights:
        #if f.aircraft_id in seen:
            f.aircraft_id=None
        #else:
        #    seen.add(f.aircraft_id)
    return new_flights

def generic_attack(correct_flights):
    # anonymize flights (by removing aircraft_id)
    flights=get_anonymized_flights(correct_flights)

    # attack mode
    future_flights=True
    side_channel=None # None
    categories=True

    # init our dicts
    ids=dict()
    mapping=dict()

    for i in range(len(flights)):
        f=flights[i]

        # get candidates for 'old' icao
        check_time=time_add([f.dep_time, timedelta(milliseconds=-1)])
        old_icaos=[a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time)]

        if f.icao in old_icaos:
            # there was most probably no change
            if f.icao not in ids:
                # unknown plane, add it
                ids[f.icao]=len(ids)
            # add mapping
            mapping[correct_flights[i].aircraft_id]=ids[f.icao]
        else:
            if len(old_icaos)==0:
                print('error',i)

            if future_flights and len(old_icaos)>0:

                if categories:
                    # attack on targetting aircraft category
                    j=i
                    while j>0 and j>i-searchWindow and len(old_icaos)>1:
                        j-=1
                        if flights[j].icao in old_icaos and flights[j].arr_airport == f.dep_airport \
                                and f.aircraft_cat != flights[j].aircraft_cat:
                            old_icaos.remove(flights[j].icao)

                # reduce old_icao by removing icao flying from the target airport in a close future
                furthest=None
                for j in range(i, int(min(i+searchWindow, len(flights)))):
                    # iterate on future flights
                    if len(old_icaos)==0:
                        # if empty list, break with only the furthest flight in time
                        old_icaos.append(furthest.icao)
                        break
                    f2=flights[j]
                    if f2.dep_airport==f.dep_airport and f2.icao in old_icaos:
                        ok=True
                        for f3 in flights[i+1:j]: # not 100% accurate
                            if f2.icao==f3.icao and f3.arr_airport==f2.dep_airport:
                                ok=False
                        if ok:
                            # if f2 is farther in future than furthest, replace it
                            if furthest is None or f2.dep_time > furthest.dep_time:
                                furthest=f2
                            old_icaos.remove(f2.icao)

            # side channel attack improvement
            if side_channel is not None:
                cst=100
                # get correct old icao
                correct_icao=None
                j=i
                while j>0 and j>i-searchWindow:
                    j-=1
                    if correct_flights[i].aircraft_id == correct_flights[j].aircraft_id:
                        correct_icao=correct_flights[j].icao
                        break
                my_list = [icao for icao in old_icaos]*cst
                if correct_icao is not None:
                    my_list += [correct_icao]*int(cst*side_channel)
                selected = random.choice(my_list)
            else:
                # random choice
                selected = random.choice(old_icaos)

            if selected not in ids:
                # aircraft never flew
                ids[selected]=len(ids)
            ids[f.icao]=ids[selected]
            del ids[selected]
        f.aircraft_id=ids[f.icao]

        if debug and mapping[correct_flights[i].aircraft_id] != f.aircraft_id:
            print('Mistake with flight:')
            print(correct_flights[i])
            print('was attributed id',f.aircraft_id)
            print('possible icaos were', old_icaos,'\n')
        
    return flights

def verify(correct, prediction):
    # check that the prediction has the same lenght as the correct sequence of flights
    if len(correct)!=len(prediction):
        print('Verification impossible')
        return 0
    
    mapping=dict()
    result=dict()
    start=correct[0].dep_time.date()
    max_time=(correct[-1].dep_time.date()-start).days
    
    for i in range(len(correct)):
        if correct[i].aircraft_id not in mapping:
            # mapping doesn't exist yet, add it
            mapping[correct[i].aircraft_id]=prediction[i].aircraft_id
            result[correct[i].aircraft_id]=max_time
        elif prediction[i].aircraft_id != mapping[correct[i].aircraft_id] and \
                result[correct[i].aircraft_id] == max_time:
            # first mistake, update successful number of days
            result[correct[i].aircraft_id] = (correct[i].dep_time.date() - start).days
        # ignore the rest (multiple mistakes)

    return result

def result_average(result):
    c=0
    for r in result:
        c+=result[r]
    return c/len(result)


def plot_results(results):
    # {id: n_days}
    count=dict()
    for aid in results:
        if results[aid] not in count:
            count[results[aid]]=0
        count[results[aid]]+=1
    data = [len(results)]
    for i in range(simlength.days):
        n=0
        if i in count:
            n=count[i]
        data.append(data[i]-n)
    plt.plot(data)
    plt.axvline(x=result_average(results), color='red')
    plt.show()

def print_flights(flights):
    for f in flights:
        print(f)

if __name__ == '__main__':
    flights = get_flights()
    guess = generic_attack(flights)
    result = verify(flights, guess)
    print(result_average(result))
    plot_results(result)
    
