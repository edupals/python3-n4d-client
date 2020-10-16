import n4d

c = n4d.Client("https://localfhost",9779)
try:
    b = c.VariablesManager.listvars()
    print(b)
except Exception as err:
    print(err)
