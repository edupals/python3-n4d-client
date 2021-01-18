import n4d.client
from getpass import getpass
import time

name=input("User:")

uk = n4d.client.Key.user_key(name)

if (uk.valid()):
    c = n4d.client.Client("https://127.0.0.1:9779",user=name,key=uk)
else:
    pwd=getpass()
    c = n4d.client.Client("https://127.0.0.1:9779",user=name,password=pwd)

r = c.validate_user()
print(r)

c.set_variable("patata",300,{"extra":400})
print(c.get_variable("patata",True))


