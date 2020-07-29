# Aircraft Privacy Simulator

This Aircraft Privacy Simulator simulates random flights for aircraft regularly changing their identifiers (call sign + ICAO address) as in the Privacy ICAO Address (PIA) program from the FAA [1]. We implemented an attack to track aircraft enrolled in the PIA program. This attack will try to track aircraft in the simulated environment and the simulation will output the success rate over time (traceability index) for the given parameters. We used data provided by OpenSky Network [2] to get US airport information.

## What's in these files ?

### [data/](data/)

Contains meta-data used by the simulator, such as lists of airports and of Privacy ICAO Addresses.

### [graphs/](graphs/)

Destination folder of the simulation output graphs.

### [records/](records/)

Destination folder of the numbers used to plot the simulation graphs. These records can be used to re-plot different graphs without having to run a new simulation.

### [attack.py](attack.py)

This file contains the tracking attack implementation. It is the main file to run to plot the traceability index of the system. All parameters of the system can be modified in the `main()` function.

### [get_airports.py](get_airports.py)

This file contains a script to fetch airports used by the simulation. Airport files are already included in the repo. This script is here only for the reference. It needs the python _traffic_ library, the installation guide can be found at [3].

### [plot.py](plot.py)

This script is used to plot graphs from older simulations without having to run them again.

### [simulation.py](simulation.py)

Contains the definition of the class Simulation. 

### [structures.py](structures.py)

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

### Modifying the attack

Feel free to improve the attack, for example by tracking the flying patterns of aircraft.

Contact: guillaume.michel@epfl.ch

### Useful resources:
[1] FAA - ADS-B Privacy - https://www.faa.gov/nextgen/equipadsb/privacy/ <br/>
[2] OpenSky Network - https://opensky-network.org/ <br/>
[3] Traffic - Installation - https://traffic-viz.github.io/installation.html
