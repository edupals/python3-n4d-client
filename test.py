import n4d

c = n4d.Client("https://localfhost",9779)
b = c.VariablesManager.listvars()
print(b)
