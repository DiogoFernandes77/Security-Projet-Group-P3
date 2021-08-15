import json
import sys
import pickle
import base64
import sys
from symetric_functions import *
from integrity_control import *
class msgCommunication:
    
    def _init_(self):
        print("msgCommunication")
    
    
    def send_data(self,clientsock,action,data ,crypt = False, key = "", origin="None", integrityKey = ""):
        info={}

        info["decode"] = False

        if crypt and key != "":
          
            if isinstance(data, list) or isinstance(data, dict):
                
                encryptedInfo = encrypt(str(data).encode(), key) #returns a list [ciphertext + iv]
            else : encryptedInfo = encrypt(data.encode(), key) #returns a list [ciphertext + iv]
            
            info["data"] = [base64.b64encode(x).decode('ascii') for x in encryptedInfo]

        else: 
            info["data"] = data

            if isinstance(data, list):
                for elem in data:
                    if isinstance(elem, bytes) :
                        info["data"] = [base64.b64encode(x).decode('ascii') for x in data]
                        info["decode"] = True


            elif isinstance(data, bytes):
                info["data"] = base64.b64encode(data).decode('ascii')
                info["decode"] = True
                    

        
        info["action"] = action
        info["origin"] = origin
        info["crypt"] = crypt
        info["hash"] = integrityKey

        if integrityKey != "":
            mac = sign_message(info["data"], integrityKey)
            info["hash"] = base64.b64encode(mac).decode('ascii')

        clientsock.send(bytes(json.dumps(info),encoding="utf8"))

    
    #client sends data to server with the respective destiny
    def send_data_dest(self,clientsock,destiny,data, crypt = False, key = "",firstTime = False, origin = "None", integrityKey = ""):
        info={}
        
        if crypt  and key != "":
            
            if isinstance(data, list) or isinstance(data, dict):
                
                encryptedInfo = encrypt(str(data).encode(), key) #returns a list [ciphertext + iv]
            else : encryptedInfo = encrypt(data.encode(), key) #returns a list [ciphertext + iv]
            
            info["data"] = [base64.b64encode(x).decode('ascii') for x in encryptedInfo]
    
        else:
        
            info["data"]=str(data)

        info["destiny"]=destiny
        info["firstTime"] = firstTime
        info["origin"] = origin
        info["hash"] = integrityKey

        if integrityKey != "":
            mac = sign_message(info["data"], integrityKey)
            info["hash"] = base64.b64encode(mac).decode('ascii')

        clientsock.send(bytes(json.dumps(info),encoding="utf8"))

  
    def receive_input(self,connection, max_buffer_size, crypt = False, key = "", decode = False, integrityKey = ""): #input received from the client

        client_input = connection.recv(max_buffer_size) #message recv from client
       
        decoded_input = client_input.decode("utf8")

        client_input_size = sys.getsizeof(client_input)
        if client_input_size > max_buffer_size:
            print("The input size is greater than expected {}".format(client_input_size))

        if integrityKey != "":
            recv_json = json.loads(decoded_input)

            mac = base64.b64decode(recv_json["hash"])
            integrity_check = verify_message(recv_json["data"], integrityKey, mac)
            if not integrity_check:
                sys.exit()

            if not crypt and not decode:
                decoded_input = recv_json["data"]

        if crypt:
            
            decoded_input = json.loads(decoded_input)
            
            encryptedInfo = [base64.b64decode(d) for d in decoded_input["data"]]
            decryptedInfo = decrypt(encryptedInfo, key)
            
            decoded_input = eval(decryptedInfo.decode('utf-8'))
        
        if decode:
            decoded_input = json.loads(decoded_input)
            if isinstance(decoded_input["data"], list):
                decoded_input = [base64.b64decode(d) for d in decoded_input["data"]]
            else:
                decoded_input = base64.b64decode(decoded_input["data"])

    
        return decoded_input

               

    def receive_inputDest(self,clientsock,crypt = False, key = "", integrityKey = ""):
        #print("Receiving some stuff...")
        recv = clientsock.recv(20480).decode()
        #print(recv)
        clientmsg = json.loads(recv)

        if integrityKey != "":
            mac = base64.b64decode(clientmsg["hash"])
            integrity_check = verify_message(clientmsg["data"], integrityKey, mac)
            if not integrity_check:
                sys.exit()
            
        if crypt:
            encrypMessage = eval(clientmsg["data"].encode("utf-8"))

            decryptedInfo = decrypt(encrypMessage, key)
            clientmsg["data"] = decryptedInfo.decode("utf8")
         
        destiny=clientmsg["destiny"]
        data=clientmsg["data"]
        firstTime = clientmsg["firstTime"]
    
        
        return destiny,data,firstTime



