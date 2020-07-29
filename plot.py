from matplotlib import pyplot as plt

# filename of the source record file
filename='records/update_freq.txt'

# graph legend
legend = 'PIA update frequency'
# filename of the exported graph
graph_filename='graphs/update_freq.pdf'
# legend for each curve
legends=['60 days', '28 days']

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

# plot graph
graph=plt.gca()
graph.set_xlim([0,len(curves[0])*1.05])
graph.set_ylim([0,1.05])
graph.legend(title=legend)
graph.set_xlabel('Days')
graph.set_ylabel('System traceability index')
plt.savefig(graph_filename)    