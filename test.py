import n4d.client

c = n4d.client.Client("https://localfhost",9779)
try:
    b = c.VariablesManager.listvars()
    print(b)
except Exception as err:
    print(err)
