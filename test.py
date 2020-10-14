import n4d

c = n4d.Client("server",9779)
b=c.VariablesManager.Get("miau",1,2)
print(b)
