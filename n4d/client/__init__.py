"""
    N4D Client

    N4D client library

    Copyright (C) 2021  Enrique Medina Gremaldos <quiqueiii@gmail.com>

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

import os

UNKNOWN_CLASS=-40
UNKNOWN_METHOD=-30
USER_NOT_ALLOWED=-20
AUTHENTICATION_ERROR=-10
INVALID_RESPONSE=-5
INVALID_ARGUMENTS=-3
UNHANDLED_ERROR=-2
CALL_FAILED=-1
CALL_SUCCESSFUL=0

class ServerError(Exception):
    def __init__(self,message):
        super().__init__(message)

class UnknownClassError(Exception):
    def __init__(self,name):
        super().__init__(self,"Class %s not found"%name)
        self.name=name

class UnknownMethodError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Method %s::%s() not found"%(name,method))
        self.name=name
        self.method=method

class UserNotAllowedError(Exception):
    def __init__(self,user,name,method):
        super().__init__(self,"%s not allowed to %s::%s()"%(user,name,method))
        self.name=name
        self.method=method
        self.user=user

class AuthenticationError(Exception):
    def __init__(self,credential):
        if (credential.auth_type==AUTH_PASSWORD or credential.auth_type==AUTH_KEY):
            super().__init__(self,"Authetication failed for user %s"%credential.user)
        elif (credential.auth_type==AUTH_ANONYMOUS):
            super().__init__(self,"Authetication failed for anonymous")
        else:
            super().__init__(self,"Authetication failed for master key")

class InvalidMethodResponseError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Invalid response from %s::%s()"%(name,method))

class InvalidServerResponseError(Exception):
    def __init__(self,server):
        super().__init__(self,"Invalid response from server %s "%server)

class InvalidArgumentsError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Invalid number of arguments for %s::%s()"%(name,method))

class UnhandledError(Exception):
    def __init__(self,name,method,traceback):
        super().__init__(self,"Unhandled error from %s::%s():\n\n%s"%(name,method,traceback))
        self.name=name
        self.method=method
        self.traceback=traceback

class CallFailedError(Exception):
    def __init__(self,name,method,code,message):
        super().__init__(self,"%s::%s() returned error code:%d\n\n%s"%(name,method,code,message))
        self.name=name
        self.method=method
        self.code=code
        self.message=message

class UnknownCodeError(Exception):
    def __init__(self,name,method,code):
        super().__init__(self,"%s::%s() returned an unknown error code:%d"%(name,method,code))

class InvalidCredentialError(Exception):
    def __init__(self,message):
        super().__init__(self,message)

class TicketFailedError(Exception):
    def __init__(self,message):
        super().__init__(self,message)

class UnknownMethodResponseError(Exception):
    def __init__(self,name,method):
        super().__init__(self,"Unknown response from %s::%s()"%(name,method))

AUTH_ANONYMOUS=1
AUTH_PASSWORD=2
AUTH_KEY=3
AUTH_MASTER_KEY=4

class Key:
    """ This class wraps the N4D key format """
    
    def __init__(self,key=""):
        """ Create a Key using a valid N4D key string """
        if (type(key)!=str):
            if (type(key)==bytes):
                self.value=key.decode("utf-8")
            else:
                self.value=""
        else:
            self.value=key
        
    def valid(self):
        """ Checks whenever the key has the proper format (50 alphanumeric cahracters) """
        if (len(self.value)==50):
            for c in self.value:
                c=ord(c)
                if (not ((c>=ord('0') and c<=ord('9')) or
                        (c>=ord('a') and c<=ord('z')) or 
                        (c>=ord('A') and c<=ord('Z')))):
                    return False
                    
            return True
        
        return False
    
    @classmethod
    def user_key(cls,user):
        """ Gets the user Key
        
        Gets the given user Key, if avaialble or possible due to access permission,
        otherwise, an empty Key is returned instead
        """
        ticket_path="/run/n4d/tickets/%s"%user
        
        return Key._load_key(ticket_path)
    
    @classmethod
    def master_key(cls):
        """ Gets the master Key
        
        Gets the master Key located at /etc/n4d if avialable or possible due to access permission,
        otherwise, an empty Key is returned instead
        """
        ticket_path="/etc/n4d/key"
        
        return Key._load_key(ticket_path)
    
    @classmethod
    def _load_key(cls,ticket_path):
        
        if (os.path.isfile(ticket_path)):
            try:
                f=open(ticket_path,"rb")
                data=f.readline()
                f.close()
                #strip possible spaces or new lines
                data=data.strip()
                
                return Key(data)
            except:
                return Key()
        else:
            return Key()
    
class Credential:
    """ A Credential class stores the authentication method and data for a N4D connection """
    
    def __init__(self,user=None,password=None,key=None):
        """ Creates a credential with given data
        
        * user + password creates a Password based credential
        * user + key creates a Key based credential
        * key creates a master Key based credential
        * with no arguments, an anonymous credential is created
        """
        
        self.auth_type=AUTH_ANONYMOUS
        
        if (user):
            if (password):
                self.auth_type=AUTH_PASSWORD
                
            if (key):
                self.auth_type=AUTH_KEY
        else:
            if (key):
                self.auth_type=AUTH_MASTER_KEY
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
            return [self.user,self.key.value]
        
        if (self.auth_type==AUTH_MASTER_KEY):
            return self.key.value

class Ticket:
    """ This class represents a N4D ticket, which is a pair of server address 
    and key based credential"""
    
    def __init__(self,ticket="",address=None,credential=None):
        """ Creates a ticket
        
        A Ticket must be created with either a string ticket, usually coming 
        from a login agent, or with both a server address and a credential 
        object. No exception is thrown, instead, an invalid Ticket is returned
        """
        self.address="https://localhost:9779"
        self.credential=Credential()

        if (type(address)==str and type(credential)==Credential):
            self.address=address
            self.credential=credential
        else:
            if (type(ticket)==str):
                tmp = ticket.split(' ')
                
                if (len(tmp)>=4):
                    if (tmp[0]=="N4DTKV2"):
                        self.address = tmp[1]
                        self.credential = Credential(user=tmp[2],key=Key(tmp[3]))
    
    def valid(self):
        """ returns True or False whenever Ticket holds a well formated Key"""
        
        return (self.credential!=None and self.credential.key.valid())
    
        
class Proxy:
    def __init__(self,client,name,method=""):
        self.client=client
        self.name=name
        self.method=method
    
    def _validate_format(self,response):
        
        if (type(response)!=dict):
            return False
        
        v = response.get("status")
        if (type(v)!=int):
            return False
        
        if (v==CALL_FAILED):
            v = response.get("error_code")
            if (type(v)!=int):
                return False
            
            if (v==UNHANDLED_ERROR):
                if (not "traceback" in response):
                    return False
            
        v = response.get("msg")
        if (type(v)!=str):
            return False
        
        if (not "return" in response):
            return False
        
        return True
    
    def call(self,*args):
        #print('call {}@{}:{}:{}()'.format(self.client.server,self.client.port,self.name,self.method,args))
        
        try:
            context=ssl._create_unverified_context()
            proxy = xmlrpc.client.ServerProxy(self.client.address,context=context)
            
            if (self.name==None):
                response = getattr(proxy,self.method)(*args)
            else:
                # method(auth,class,args...)
                response = getattr(proxy,self.method)(self.client.credential.get(),self.name,*args)
            
        except Exception as err:
            raise ServerError(str(err))
        
        #print(response)
        
        if (self._validate_format(response)):
            status=response["status"]
            
            if (status==UNKNOWN_CLASS):
                raise UnknownClassError(self.name)
            
            if (status==UNKNOWN_METHOD):
                raise UnknownMethodError(self.name,self.method)
            
            if (status==USER_NOT_ALLOWED):
                raise UserNotAllowedError(self.client.credential.user,self.name,self.method)
            
            if (status==AUTHENTICATION_ERROR):
                raise AuthenticationError(self.client.credential)
            
            if (status==INVALID_RESPONSE):
                raise InvalidMethodResponseError(self.name,self.method)
            
            if (status==INVALID_ARGUMENTS):
                raise InvalidArgumentsError(self.name,self.method)
            
            if (status==UNHANDLED_ERROR):
                raise UnhandledError(self.name,self.method,response["traceback"])
            
            if (status==CALL_FAILED):
                raise CallFailedError(self.name,self.method,response["error_code"],response["msg"])
            
            if (status==CALL_SUCCESSFUL):
                return response["return"]
            else:
                raise UnknownCodeError(self.name,self.method,status)
            
        else:
            #print(response)
            raise InvalidServerResponseError(self.client.server)
        
        
        
    def __call__(self, *args):
    # calling Proxy as built in method
        self.method=self.name
        self.name=None
        
        return self.call(*args)
        
    def __getattr__(self,method):
        self.method=method
        return self.call
    
class Client:
    """ Performs N4D calls 
    
    A client is constructed using a combination of user, password, key or 
    ticket.
    
    Client will create a proper Credential using given user/password/key.
    A Client can also be constructed from a single Ticket object.
    """
    def __init__(self,address="https://127.0.0.1:9779",user=None,password=None,key=None,ticket=None):
        
        if (ticket!=None and ticket.valid()):
            self.address = ticket.address
            self.credential = ticket.credential
        else:
            self.address=address
            self.credential=Credential(user,password,key)
    
    def create_ticket(self):
        """ Requests N4D server a ticket for user stored in Client credential.
        
        The ticket will be created and stored in local machine, then this method
        will attempt to read it.
        If credential is not Password or Key type, It will raise a exception.
        If Ticket does not exists or cannot be access, and empty Ticket is 
        returned instead.
        """
        if (self.credential.auth_type==AUTH_PASSWORD or self.credential.auth_type==AUTH_KEY):
            p = Proxy(self,None,"create_ticket")
            status = p.call(self.credential.user)
            
            return Ticket(address=self.address,credential=Credential(user=self.credential.user,key=Key.user_key(self.credential.user)))
        else:
            raise InvalidCredentialError("Expected password credential")
    
    def get_ticket(self):
        """ Requests N4D server a ticket for user stored in Client credential.
        
        This ticket is not stored in any place, just on server and client app.
        If credential is not Password or Key type, It will raise a exception.
        If Ticket does not exists or cannot be access, and empty Ticket is 
        returned instead.
        """
        if (self.credential.auth_type==AUTH_PASSWORD):
            p = Proxy(self,None,"get_ticket")
            value = p.call(self.credential.user,self.credential.password)
            
            return Ticket(address=self.address,credential=Credential(user=self.credential.user,key=Key(value)))
        else:
            raise InvalidCredentialError("Expected password credential")

    def validate_user(self):
        if (self.credential.auth_type==AUTH_PASSWORD):
            p = Proxy(self,None,"validate_user")
            return p.call(self.credential.user,self.credential.password)
        elif (self.credential.auth_type==AUTH_KEY):
            p = Proxy(self,None,"validate_user")
            return p.call(self.credential.user,self.credential.key.value)
        else:
            raise InvalidCredentialError("Expected password or key credential")
        
    def get_methods(self):
        p = Proxy(self,None,"get_methods")
        return p.call()
    
    def get_variable(self,name,info = False):
        p = Proxy(self,None,"get_variable")
        return p.call(name,info)
    
    def set_variable(self,name,value,extra_info = None):
        p = Proxy(self,None,"set_variable")
        return p.call(self.credential.get(),name,value,extra_info)
    
    def delete_variable(self,name):
        p = Proxy(self,None,"delete_variable")
        return p.call(self.credential.get(),name)
        
    def get_variables(self,full_info = False):
        p = Proxy(self,None,"get_variables")
        return p.call(full_info)
    
    def version(self):
        p = Proxy(self,None,"version")
        return p.call()
        
    def __getattr__(self,name):
        return Proxy(self,name)
    
