import xmlrpc.client
import ssl

UNKNOWN_CLASS=-40
UNKNOWN_METHOD=-30
USER_NOT_ALLOWED=-20
AUTHENTICATION_ERROR=-10
INVALID_RESPONSE=-5
INVALID_ARGUMENTS=-3
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
    def __init__(self,user):
        super().__init__(self,"Authetication failed for user %s"%user)
        
class InvalidMethodResponseError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Invalid response from %s::%s()"%(name,method))

class InvalidServerResponseError(Exception):
    def __init__(self,server):
        super().__init__(self,"Invalid response from server %s "%server)

class InvalidArgumentsError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Invalid number of arguments for  %s::%s()"%(name,method))

class CallFailedError(Exception):
    def __init__(self,name,method,code):
        super().__init__(self,"%s::%s() returned error code:%d"%(name,method,code))

class UnknownCodeError(Exception):
    def __init__(self,name,method,code):
        super().__init__(self,"%s::%s() returned an unknown error code:%d"%(name,method,code))

AUTH_ANONYMOUS=1
AUTH_PASSWORD=2
AUTH_KEY=3

class Credential:
    def __init__(self,user=None,password=None,key=None):

        if (user):
            if (password):
                self.auth_type=AUTH_PASSWORD
                
            if (key):
                self.auth_type=AUTH_KEY
        else:
            self.auth_type=AUTH_ANONYMOUS
        
        self.user=user
        self.password=password
        self.key=key
        
    def get(self):
        if (self.auth_type==AUTH_ANONYMOUS):
            return ""
        
        if (self.auth_type==AUTH_PASSWORD):
            return [self.user,self.password]
        
        if (self.auth_type==AUTH_KEY):
            return [self.user,self.key]
    
class Proxy:
    def __init__(self,client,name):
        self.client=client
        self.name=name
    
    def _validate_response(self,response):
        
        if (type(response)!=dict):
            return False
        
        v = response.get("msg")
        if (type(v)!=str):
            return False
        
        v = response.get("status")
        if (type(v)!=int):
            return False
        
        v = response.get("return")
        if (v==None):
            return False
        
        return True
    
    def call(self,*args):
        #print("call "+self.client.server+"@"+str(self.client.port)+":"+self.name+":"+self.method+"("+str(args)+")")
        
        try:
            context=ssl._create_unverified_context()
            proxy = xmlrpc.client.ServerProxy("%s:%d"%(self.client.server, self.client.port),context=context)
            
            # method(auth,class,args...)
            response = getattr(proxy,self.method)(self.client.credential.get(),self.name,*args)
            
            if (self._validate_response(response)):
                status=response["status"]
                
                if (status==UNKNOWN_CLASS):
                    raise UnknownClassError(self.name)
                
                if (status==UNKNOWN_METHOD):
                    raise UnknownMethodError(self.name,self.method)
                
                if (status==USER_NOT_ALLOWED):
                    raise UserNotAllowedError(self.client.credential.user,self.name,self.method)
                
                if (status==AUTHENTICATION_ERROR):
                    raise AuthenticationError(self.client.credential.user)
                
                if (status==INVALID_RESPONSE):
                    raise InvalidMethodResponseError(self.name,self.method)
                
                if (status==INVALID_ARGUMENTS):
                    raise InvalidArgumentsError(self.name,self.method)
                    
                if (status==CALL_FAILED):
                    # hardcoded -1
                    raise CallFailedError(self.name,self.method,-1)
                else:
                    raise UnknownCodeError(self.name,self.method,status)
                
            else:
                raise InvalidServerResponseError(self.client.server)
        
        except Exception as err:
            raise ServerError(str(err))

        return response["return"]
    
    def __getattr__(self,method):
        self.method=method
        return self.call
    
class Client:
    def __init__(self,server,port,user=None,password=None,key=None):
        self.server=server
        self.port=port
        self.credential=Credential(user,password,key)
    
    def __getattr__(self,name):
        return Proxy(self,name)
    
