import n4d.client
from getpass import getpass
import time

name=input("User:")
pwd=getpass()

c = n4d.client.Client("https://127.0.0.1",9800,user=name,password=pwd)

try:
    r = c.validate_user()
    print(r)
    
    c.set_variable("patata",300,"")
    times=[]
    
    a1=time.time()
    for n in range(1000):
        d1=time.time()
        r = c.get_variable("patata")
        d2=time.time()
        times.append(d2-d1)
    a2=time.time()
    
    print(r)
    
    for n in range(len(times)):
        print("%s %f ms"%(n,1000*times[n]))
    
    print("total %f seconds"%(a2-a1))
    #r = c.get_methods()
    #print(r)
    
except Exception as err:
    print(err)
