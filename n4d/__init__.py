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
    def __init__(self,name,method):
        super().__init__(self,"Method %s::%s() not found"%(name,method))

class UserNotAllowedError(Exception):
    def __init__(self,user,name,method):
        super().__init__(self,"%s not allowed to %s::%s()"%(user,name,method))

class AuthenticationError(Exception):
    def __init__(self,name):
        super().__init__(self,"Authetication failed for user %s"%name)
        
class InvalidMethodResponseError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Invalid response from %s::%s()"%(name,method))

class InvalidServerResponseError(Exception):
    def __init__(self,server):
        super().__init__(self,"Invalid response from server %s "%server)

AUTH_ANONYMOUS=1
AUTH_PASSWORD=2
AUTH_KEY=3

class Credential:
    def __init__(self,user=None,password=None,key=None):

        self.auth_type=AUTH_ANONYMOUS

        if (user and password):
            self.auth_type=AUTH_PASSWORD
            
        if (key):
            self.auth_type=AUTH_KEY
        
        self.user=user
        self.password=password
        self.key=key
    
class Proxy:
    def __init__(self,client,name):
        self.client=client
        self.name=name
    
    def call(self,*args):
        print("call "+self.client.server+"@"+str(self.client.port)+":"+self.name+":"+self.method+"("+str(args)+")")
        server = SimpleXMLRPCServer((self.client.server, self.client.port))
        
        response = server.do()
        
        if (("msg" in response) and ("status" in response) and ("return" in response)):
            status=response["status"]
            
            if (status==UNKNOWN_CLASS):
                raise UnknownClassError(self.name)
            
            if (status==UNKNOWN_METHOD):
                raise UnknownMethodError(self.name,self.method)
            
            if (status==USER_NOT_ALLOWED):
                pass
            
            if (status==AUTHENTICATION_ERROR):
                pass
            
            if (status==INVALID_RESPONSE):
                raise InvalidMethodResponseError(self.name,self.method)
        else:
            raise InvalidServerResponseError()
        
        return response["return"]
    
    def __getattr__(self,method):
        self.method=method
        return self.call
    
class Client:
    
    def __init__(self,server,port):
        self.server=server
        self.port=port
    
    def __getattr__(self,name):
        return Proxy(self,name)
    
