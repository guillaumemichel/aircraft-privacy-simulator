from distributions import Distribution
from structures import *
from copy import deepcopy
from matplotlib import pyplot as plt

sys.setrecursionlimit(10000)

n_aircraft=100 # 1062 available icaos in total or parameter range in structures.py
airports=airports_from_file('large').first(100)

individual_flight_freq=0.31 # in days
intervals=24*60/individual_flight_freq/n_aircraft # in minutes
searchWindow=30*24*60/intervals

flight_frequency=timedelta(minutes=intervals)
n_categories=1
mode='random'
#policy='20-days' # no_privacy, callsign-change, 60-days, 20-days, max_privacy
simlength=timedelta(days=365)

debug=False

random.seed('0')

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

def generic_attack(correct_flights, future_flights=True, side_channel=None, \
        categories=True, lost_airports_n=0):
    # anonymize flights (by removing aircraft_id)
    flights=get_anonymized_flights(correct_flights)
    lost_airports=random.choices(population=airports.elements, k=lost_airports_n)
    #print('lost_airports',lost_airports)

    change_detected=0
    mistakes=0

    # init our dicts
    ids=dict()
    mapping=dict()

    for i in range(len(flights)):
        f=flights[i]

        # get candidates for 'old' icao
        check_time=time_add([f.dep_time, timedelta(microseconds=-1)])

        if f.dep_airport.icao in [a.icao for a in lost_airports]:
            # check lost airport
            old_icaos=[ac.icao_at(check_time) for ap in lost_airports for ac in ap.aircraft_at(check_time) if ac.cat==f.aircraft_cat]
        else:
            #old_icaos=[a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time)]
            old_icaos=[a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time) if a.cat==f.aircraft_cat]

        if f.icao in old_icaos:
            # there was most probably no change
            if f.icao not in ids:
                # unknown plane, add it
                ids[f.icao]=len(ids)
        else:
            change_detected+=1
            if len(old_icaos)==0:
                print('error',i)
                print([a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time) if a.cat==f.aircraft_cat])
                print([a.icao_at(check_time) for a in f.dep_airport.aircraft_at(check_time)])
                print(f.dep_airport.icao)
                print(f.dep_time)
                print(correct_flights[i].aircraft_id)

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

        # add mapping
        if correct_flights[i].aircraft_id not in mapping:
            mapping[correct_flights[i].aircraft_id]=ids[f.icao]


        if mapping[correct_flights[i].aircraft_id] != f.aircraft_id:
            mistakes+=1
            if debug:
                print('Mistake with flight:')
                print(correct_flights[i])
                print('was attributed id',f.aircraft_id)
                print('possible icaos were', old_icaos,'\n')
        
    #print(change_detected,'changes detected')
    #print(mistakes, 'mistakes')
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

def multiple_sim(n=10, future_flights=True, side_channel=None, \
        categories=True, lost_airports_n=0, label='No label'):
    results=list()
    for i in range(n):
        flights = get_flights()
        guess = generic_attack(flights, future_flights=future_flights, \
            side_channel=side_channel, categories=categories, lost_airports_n=lost_airports_n)
        results.append(verify(flights, guess))

    final=[0]*simlength.days
    for result in results:
        count=dict()
        for aid in result:
            if result[aid] not in count:
                count[result[aid]]=0
            count[result[aid]]+=1
        data = [1.0]
        for i in range(simlength.days):
            m=0
            if i in count:
                m=count[i]
            data.append(data[i]-(m/len(result)))
            final[i]+=data[-1]
    final=[e/n for e in final]
    to_file('records/aircraft.txt', final)
    plt.plot(final, label=label)

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
    data = [1.0]
    for i in range(simlength.days):
        n=0
        if i in count:
            n=count[i]
        data.append((data[i]-n)/len(results))
    plt.plot(data)
    plt.gca().set_xlim([0,simlength.days*1.05])
    plt.gca().set_ylim([0,n_aircraft*1.1])
    to_file('records/together2.txt', data)
    #plt.axvline(x=result_average(results), color='red')
    #plt.show()

def to_file(filename, struct):
    f = open(filename, 'a')
    f.write(str(struct)+'\n')
    f.close()

def print_flights(flights):
    for f in flights:
        print(f)

if __name__ == '__main__':
    #policy = 'no_privacy'
    #multiple_sim(n=20, label='no_privacy')
    n_aircraft=10
    airports=airports_from_file('large').first(45)
    policy = '28-days'
    n_categories=1
    multiple_sim(n=100, label='28 days')
    policy = '60-days'
    multiple_sim(n=100, label='60 days')
    #policy = 'max_privacy'
    #multiple_sim(n=100, label='max privacy')

    graph=plt.gca()
    graph.set_title('Tracked aircraft over time')
    graph.set_xlim([0,simlength.days*1.05])
    #graph.set_ylim([0,n_aircraft*1.1])
    graph.set_ylim([0,1.05])
    graph.legend(title='PIA update frequency')
    graph.set_xlabel('Days')
    graph.set_ylabel('Tracked aircraft rate')
    plt.savefig('graphs/graph.pdf')

    """
    policy = '20-days'
    flights = get_flights()
    guess = generic_attack(flights)
    result = verify(flights, guess)
    #plot_results(result)

    policy = 'max_privacy'
    flights = get_flights()
    guess = generic_attack(flights)
    result = verify(flights, guess)
    #plot_results(result)

    plt.savefig('graph.pdf')
    """
    """
    #n_aircraft=500 # 1062 available icaos in total or parameter range in structures.py
    #airports=airports_from_file('large').first(100)
    #flight_frequency=timedelta(minutes=intervals)
    n_categories=2
    #mode='random'
    policy='60-days' # no_privacy, callsign-change, 60-days, 20-days, max_privacy
    #simlength=timedelta(days=90)

    flights = get_flights()
    guess = generic_attack(flights)
    result = verify(flights, guess)
    print(result_average(result))
    plot_results(result)

    plt.savefig('graph.jpg')

    """
