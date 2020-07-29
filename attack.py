from simulation import Simulation
from structures import *
from copy import deepcopy
from matplotlib import pyplot as plt

sys.setrecursionlimit(10000)

# create a simulation and get the list of flights that resulted from it
def get_flights(mode='random', policy='max_privacy', airports=None, n_aircraft=100, \
        flight_frequency=0.31, n_categories=1, simlength=timedelta(days=30)):

    # if no airports are given, take the default ones
    if airports is None:
        airports=airports_from_file('large').first(100)
    
    # create the simulation
    dis = Simulation(mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency, \
        n_categories=n_categories)
    # run the simulation and returns the results of the simulation
    return dis.run(simlength)    

# get all flights without unique identifier
def get_anonymized_flights(flights):
    new_flights = deepcopy(flights)
    for f in new_flights:
            f.aircraft_id=None
    return new_flights

# perform the tracking attack on the given flights
def generic_attack(correct_flights, future_flights=True, side_channel=None, \
        categories=True, lost_airports_n=0, searchWindow=30/0.31):
    # anonymize flights (by removing aircraft_id)
    flights=get_anonymized_flights(correct_flights)
    lost_airports=random.choices(population=airports.elements, k=lost_airports_n)

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
        
    return flights

# verify the correctness of a given prediction
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

def multiple_sim(n=1, mode='random', policy='max_privacy', airports=None, \
        n_aircraft=100, flight_frequency=0.31, n_categories=1, \
        simlength=timedelta(days=30), future_flights=True, side_channel=None, \
        categories=True, lost_airports_n=0, searchWindow=30/0.31, \
        record_file='records/record.txt',label='No label'):

    statement="Starting new simulation"
    status=" "
    print(statement,end="\r")

    results=list()
    for i in range(n):
        # create the random flight list by simulation
        flights = get_flights(mode=mode, policy=policy, airports=airports, \
            n_aircraft=n_aircraft, flight_frequency=flight_frequency, \
            n_categories=n_categories, simlength=simlength)
        # attack to track aircraft
        guess = generic_attack(flights, future_flights=future_flights, \
            side_channel=side_channel, categories=categories, \
            lost_airports_n=lost_airports_n, searchWindow=searchWindow)
        # verify correctness of the guess
        results.append(verify(flights, guess))
        if i%10==9:
            status+='|'
        else:
            status+='.'
        print(statement+status,end="\r")

    # get average of the n simulations
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
    # write average to file
    to_file(record_file, final)
    # plot average
    plt.plot(final, label=label)

    print(statement+status+" done!")

# plot results of simulations
def plot_results(legend='Example legend', graphfile='graphs/graph.pdf'):
    graph=plt.gca()
    graph.set_xlim([0,simlength.days*1.05])
    graph.set_ylim([0,1.05])
    graph.legend(title=legend)
    graph.set_xlabel('Days')
    graph.set_ylabel('Traceability index')
    plt.savefig(graphfile)

# write data to file
def to_file(filename, struct):
    f = open(filename, 'a')
    f.write(str(struct)+'\n')
    f.close()

# print flights for debug
def print_flights(flights):
    for f in flights:
        print(f)

debug=False
random.seed('random')

if __name__ == '__main__':

    ### PARAMETER DEFINITION ###

    # Simulation mode (other simulation modes not available yet)
    mode='random'
    # Number of aircraft in the simulation
    n_aircraft=100
    # Airports in the simulation (taken from lists in data/ )
    airports=airports_from_file('large').first(100)
    # Distinct categories of aircraft an adversary can distinguish
    n_categories=1
    # Average flight frequency of aircraft (flight per day per aircraft)
    flight_frequency=0.31
    # Duration of the simulation
    simlength=timedelta(days=365)
    # PIA update policy (available policies 'no_privacy', '{int}-days', 
    # '{int}-days-simultaneous', 'callsign-change', 'max_privacy')
    policy = '60-days'
    # Filename of the record file containing the average privacy index values
    record_file='records/60-days.txt'
    # Label of the simulation curve on the graph
    label='60 days'

    ### SIMULATION 1 ###

    multiple_sim(n=2, mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency, \
        n_categories=n_categories, simlength=simlength, \
        record_file=record_file, label=label)

    ### UPDATE PARAMETERS ###

    policy = '28-days'
    #record_file='records/28-days.txt'
    label='28 days'

    ### SIMULATION 2 ###

    multiple_sim(n=2, mode=mode, policy=policy, airports=airports, \
        n_aircraft=n_aircraft, flight_frequency=flight_frequency, \
        n_categories=n_categories, simlength=simlength, \
        record_file=record_file, label=label)

    ### PLOT RESULTS ###

    plot_results(legend='PIA update frequency', graphfile='graphs/update_freq.pdf')