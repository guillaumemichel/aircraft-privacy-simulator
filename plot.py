from matplotlib import pyplot as plt

filename='records/max_privacy.txt'

parameter = 'PIA update frequency'
legends=['60 days', '28 days', 'each flight']

f=open(filename, 'r')
data=f.read()
f.close()

curves=list()
for l in data.split('\n'):
    if len(l)==0:
        break
    curves.append([float(d.strip()) for d in l.replace('[', '').replace(']', '').split(',')[:-1]])

if len(curves)!=len(legends):
    print('error with legends')

for i in range(len(curves)):
    plt.plot(curves[i],label=legends[i])

graph=plt.gca()
#graph.set_title('Tracked aircraft over time')
graph.set_xlim([0,len(curves[0])*1.05])
#graph.set_ylim([0,n_aircraft*1.1])
graph.set_ylim([0,1.05])
graph.legend(title=parameter)
graph.set_xlabel('Days')
graph.set_ylabel('System traceability index')
plt.savefig('graphs/graphtest.pdf')    