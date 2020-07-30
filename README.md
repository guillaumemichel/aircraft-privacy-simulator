# Aircraft Privacy Simulator

This Aircraft Privacy Simulator simulates random flights for aircraft regularly changing their identifiers (call sign + ICAO address) as in the Privacy ICAO Address (PIA) program from the FAA [1]. We implemented an attack to track aircraft enrolled in the PIA program. This attack will try to track aircraft in the simulated environment and the simulation will output the success rate over time (traceability index) for the given parameters. We used data provided by OpenSky Network [2] to get US airport information.

## What's in these files ?

* ### [data/](data/)

Contains meta-data used by the simulator, such as lists of airports and of Privacy ICAO Addresses.

* ### [graphs/](graphs/)

Destination folder of the simulation output graphs.

* ### [records/](records/)

Destination folder of the numbers used to plot the simulation graphs. These records can be used to re-plot different graphs without having to run a new simulation.

* ### [attack.py](attack.py)

This file contains the tracking attack implementation. It is the main file to run to plot the traceability index of the system. All parameters of the system can be modified in the `main()` function.

* ### [get_airports.py](get_airports.py)

This file contains a script to fetch airports used by the simulation. Airport files are already included in the repo. This script is here only for the reference. It needs the python _traffic_ library, the installation guide can be found at [3].

* ### [plot.py](plot.py)

This script is used to plot graphs from older simulations without having to run them again.

* ### [simulation.py](simulation.py)

Contains the definition of the class Simulation. 

* ### [structures.py](structures.py)

Contains all structures that are used mainly by [attack.py](attack.py) and [simulation.py](simulation.py).

## How can I use this ?

Make sure to have python 3.x installed.

```bash
git clone https://github.com/guillaumemichel/aircraft-privacy-simulator/
cd aircraft-privacy-simulator
python attack.py
```

The script may take a few minutes to run and will output a plot in the [graphs/](graphs/) folder and its associated data in [records/](records/).

You can then modify the Simulation parameters in [attack.py](attack.py) to get a customized simulation.

### Modifying simulation parameters

#### Mode

```python
# Simulation mode (other simulation modes not available yet)
mode='random'
```
Simulation mode to simulate flights. Only _random_ mode available yet, more realistic flight models may be added.

#### Aircraft Number
```python
# Number of aircraft in the simulation
n_aircraft=100
```

Number of aircraft in the simulation. All aircraft use the same call sign and ICAO address range. The global privacy level increases when the number of simulated aircraft grows.

#### Airports
```python
# Airports in the simulation (taken from lists in data/ )
airports=airports_from_file('large').first(100)
```
Set of airports used by the simulation. [data/](data/) contains 3 lists of airports _small_, _medium_ and _large_ airports located in the US. The given line takes the 100 first airports from the list of _large_ US airports. The global privacy level decreases when the number of airports in the set grows.

#### Number of aircraft categories

```python
# Distinct categories of aircraft an adversary can distinguish
n_categories=1
```

An attacker could be able to distinguish among multiple aircraft types as described in [4]. This parameter represents the number of aircraft types an adversary is able to distinguish by looking at basic ADS-B transmissions, such as acceleration, velocity etc. The global privacy level decreases when the number of aircraft categories that an adversary can distinguish grows.

#### Flight frequency

```python
# Average flight frequency of aircraft (flight per day per aircraft)
flight_frequency=0.31
```

Average number of flights per day per aircraft. This frequency has been computed from a data set of private aircraft in the US.

#### Simulation duration
```python
# Duration of the simulation
simlength=timedelta(days=365)
```
Duration of the simulation (here in days).

#### Policy
```python
# PIA update policy (available policies 'no_privacy', '{int}-days', 
# '{int}-days-simultaneous', 'callsign-change', 'max_privacy')
policy = '60-days'
```

PIA update policy used by the simulation. The following policies are available:

* ##### No privacy (_no\_privacy_)

When this policy is used, aircraft never change their ICAO addresses nor call signs.

* ##### Call sign change (_callsign-change_)

When this policy is used, aircraft never update their ICAO address, but they change call sign for each flight.

* ##### XX days (eg. _60-days_)

When this policy is used, aircraft update their call sign for each flight, and they change their ICAO address every _XX_ days. The first date of ICAO address change is picked at random for each aircraft. _60-days_ corresponds to the PIA program in phase 1, and _28-days_ corresponds to the PIA program in phase 2.

* ##### XX days simultaneous (_XX-days-simultaneous)

When this policy is used, aircraft update their call sign for each flight. All aircraft change their ICAO address every _XX_ days, simultaneously. This policy provides a better privacy protection than the _XX-days_ policy, as it maximizes the number of aircraft updating their ICAO address at the same airport during the same time period.

* ##### Max privacy

This policy provied the best theoretical privacy performance, without modifying aircraft trajectories. When this policy is used, aircraft update their call sign and ICAO address for each flight.

#### Filename
```python
# Filename of the record file containing the average privacy index values
record_file='records/update_freq.txt'
```
Filename of the record file containing the average privacy index values. 

#### Label
```python
# Label of the simulation curve on the graph
label='60 days'
```
Name of the curve representing the simulation on the exported plot.

### Modifying the attack

Feel free to improve the attack, for example by tracking the flying patterns of aircraft.

## Useful resources:
[1] FAA - ADS-B Privacy - https://www.faa.gov/nextgen/equipadsb/privacy/ \
[2] OpenSky Network - https://opensky-network.org/ \
[3] Traffic - Installation - https://traffic-viz.github.io/installation.html \
[4] M. Strohmeier, M. Smith, V. Lenders, and I. Martinovic, “Classi-fly: Inferring aircraftcategories from open data,”arXiv preprint arXiv:1908.01061, August 2019.

Contact: guillaume.michel@epfl.ch
