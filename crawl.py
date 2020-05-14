filename='records/policies.txt'

f=open(filename, 'r')
data=f.read()
f.close()

def get_first_value(v):
    c = 0
    for d in curves[1]:
        c+=1
        if d < v:
            print(c)
            break

def get_value_at(i):
    print(curves[0][i])

curves=list()
for l in data.split('\n'):
    if len(l)==0:
        break
    curves.append([float(d.strip()) for d in l.replace('[', '').replace(']', '').split(',')[:-1]])

get_value_at(250)