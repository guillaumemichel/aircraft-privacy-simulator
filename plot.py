from matplotlib import pyplot as plt

filename='records/airports_0.txt'

f=open(filename, 'r')
data=f.read()
f.close()

curves=list()
for l in data.split('\n'):
    print('coucou')
    print(l)
    #data = [float(d.strip()) for d in l.replace('[', '').replace(']', '').split(',')]

graph=plt.gca()
graph.set_title('Tracked aircraft over time')
graph.set_xlim([0,len(curves)*1.05])
#graph.set_ylim([0,n_aircraft*1.1])
graph.set_ylim([0,1.05])
graph.legend(title='Number of airports')
graph.set_xlabel('Days')
graph.set_ylabel('Tracked aircraft rate')
plt.savefig('graphs/graph0pyth.pdf')    