import n4d

c = n4d.Client("https://localhost",9779)
b = c.VariablesManager.listvars()
print(b)
