import n4d.client
from getpass import getpass
import time

name=input("User:")
pwd=getpass()

c = n4d.client.Client("https://127.0.0.1:9800",user=name,password=pwd)

r = c.validate_user()
print(r)

c.set_variable("patata",300,{"extra":400})
print(c.get_variable("patata",True))


