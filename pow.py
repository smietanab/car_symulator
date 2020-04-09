
def SetSignall(array, SignallName, value):
    p = 0
    leng  = SignallName[1]
    pos  = SignallName[0]

    for i in range(pos,pos+leng):
        byte = i//8
        bit = i%8
        temp = value >> p & 1

        if temp != 0:
            array[byte] |= 1 << bit;
        else:
            array[byte] &= ~(1 << bit)
        p=p+1




def ReadSignall(array, SignallName):
    leng  = SignallName[1]
    pos  = SignallName[0]
    p = 0
    value_to_return = 0
    shortValue = 0
    j = 0
    for i in range(pos,pos+leng):
        byte = i//8;
        bit = i%8;
        if ((array[byte] & (1 << bit)) != 0):
            pow = 2**(p%8)
            #if(pow < 256):
            shortValue  = shortValue + pow
        if((p%8) == 7):
            value_to_return= value_to_return + (shortValue << j)
            shortValue = 0
            j = j+8
        p = p+1
    value_to_return = value_to_return + (shortValue << j)
    return value_to_return

u = [0,0,0,0,0,0,0,0]

SetSignall(u, (4,4), 0x0E)
SetSignall(u, (0,4), 0x0E)
print(u)
i = ReadSignall(u, (4,4))
print(hex(i))
i = ReadSignall(u, (0,4))
print(hex(i))
