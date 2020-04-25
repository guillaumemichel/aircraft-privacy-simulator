mod=7

def get_seq(low, high):
    if low <= high:
        seq=set(range(low, high+1))
    else:
        seq=set(range(low, mod+1))
        seq.update(set(range(0,high+1)))
    return seq

seq0=get_seq(2,3)
seq1=get_seq(6,7)
seq2=seq0&seq1
print(len(seq2)==0)