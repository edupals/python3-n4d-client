import xmlrpc.client

UNKNOWN_CLASS=-40
UNKNOWN_METHOD=-30
USER_NOT_ALLOWED=-20
AUTHENTICATION_ERROR=-10
INVALID_RESPONSE=-5
CALL_FAILED=-1
CALL_SUCCESSFUL=0

class ServerError(Exception):
    def __init__(self,message):
        super().__init__(message)

class UnknownClassError(Exception):
    def __init__(self,name):
        super().__init__(self,"Class %s not found"%name)

class UnknownMethodError(Exception):
    def __init__(self,name):
        super().__init__(self,"Method %s not found"%name)

class AuthenticationError(Exception):
    def __init__(self,name):
        super().__init__(self,"Authetication failed for user %s"%name)
        
class InvalidMethodResponseError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Invalid response from %s::%s()"%(name,method))

class InvalidServerResponseError(Exception):
    def __init__(self,server):
        super().__init__(self,"Invalid response from server %s "%server)

class Proxy:
    def __init__(self,client,name):
        self.client=client
        self.name=name
    
    def call(self,*args):
        print("call "+self.client.server+"@"+str(self.client.port)+":"+self.name+":"+self.method+"("+str(args)+")")
        server = SimpleXMLRPCServer((self.client.server, self.client.port))
        
        response = server.do()
        
        return response
    
    def __getattr__(self,method):
        self.method=method
        return self.call
    
class Client:
    
    def __init__(self,server,port):
        self.server=server
        self.port=port
    
    def __getattr__(self,name):
        return Proxy(self,name)
    
