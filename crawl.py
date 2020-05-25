filename='records/together.txt'

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

def get_value_at(i, curve):
    print(curves[curve][i])

def get_average():
    print(sum(curves[0])/len(curves[0]))
    

curves=list()
for l in data.split('\n'):
    if len(l)==0:
        break
    curves.append([float(d.strip()) for d in l.replace('[', '').replace(']', '').split(',')[:-1]])

get_value_at(90, 2)
get_value_at(90, 0)