"""
N4D Client

N4D client library

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

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
    def __init__(self,name,method,code,message):
        super().__init__(self,"%s::%s() returned error code:%d"%(name,method,code))
        self.code=code
        self.message=message

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
        
        v = response.get("status")
        if (type(v)!=int):
            return False
        
        if (v==CALL_FAILED):
            v = response.get("error_code")
            if (type(v)!=int):
                return False
        
        v = response.get("msg")
        if (type(v)!=str):
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
                    raise CallFailedError(self.name,self.method,response["error_code"],response["msg"])
                
                if (status==CALL_SUCCESSFUL):
                    return response["return"]
                else:
                    raise UnknownCodeError(self.name,self.method,status)
                
            else:
                raise InvalidServerResponseError(self.client.server)
        
        except Exception as err:
            raise ServerError(str(err))
        
        # def call
    
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
    
