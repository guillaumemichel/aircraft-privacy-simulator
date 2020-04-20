from structures import categories, from_opensky, Airports
from traffic.data import airports
import sys

for cat in categories:
    airports = get_us_airports(cat=cat)
    airports.to_file('data/'+cat+'_airports.json')


def get_us_airports(cat='large'):
    """
    Get a list of US airports.
    - Category large will return only large airports of continental US (icao starting with K)
    - Category medium will return medium and large airports which icao start with K
    - Category small will return small, medium and large airports starting with K
    - Category all with retrun all active small, medium and large US airports including
    Alaska, Guam etc.
    """
    index = categories.index(cat)
    if index < 0:
        print('Invalid airport category: '+str(cat))
        sys.exit(1)

    us_airports = Airports()
    for (_,a) in airports.data.iterrows():
        if a[5]=='United States' and 'airport' in a[7]:

            if index < 3:
                valid = a[2][0]=='K'
                for c in a[2][1:]:
                    if not ord('A')<=ord(c)<=ord('Z'):
                        valid=False
                if not valid:
                    continue
                
                found = False
                for c in categories[:index+1]:
                    if c in a[7]:
                        found=True

                if not found:
                    continue

            us_airports.append(from_opensky(a))
    return us_airports