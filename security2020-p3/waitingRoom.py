
import threading
import sys
import json
import pickle
from send_receive import *
from cryptoAssym import *
from cryptography . hazmat . primitives . asymmetric import rsa
from cartaocidadao import *

class waitingRoom():

    def __init__(self,privKey,pubKey): #só chave pública, pq a waiting room não precisa de decifrar nenhuma mensagem proveniente do cliente
        self.d = {}
        self.lobbyLock=list()
        self.logged=0

        self.pubKey = pubKey
        self.privKey = privKey
        self.publicKeys = {}
        self.symetricKeys = list()
        self.msg=msgCommunication()

        #Citizen Card
        #self.cc_disabler = 0
        self.usernames_sock = {}

    def logging(self,clientsock):

        #username="server"
        #loggIn=self.log_in_data(username)
        #while (True,1) or (False)
        print("Asking for username")
        self.msg.send_data(clientsock,"Auth","\nUsername:" )
        username = self.receive_input(clientsock, 1024) 
        print(username)
        self.usernames_sock.update({clientsock:username})
        loggIn=self.log_in_data(username)

        while(not loggIn): #LOGIN
            print("Asking for username")
            self.msg.send_data(clientsock,"Auth","\nUsername:" )
            username = self.receive_input(clientsock, 1024) 
            print(username)
            loggIn=self.log_in_data(username)

        self.d.update({username:0})
        self.logged+=1
        self.msg.send_data(clientsock,"Auth","Logged Sucessufully")
        print(self.receive_input(clientsock, 1024))

        # #authenticate
        self.msg.send_data(clientsock, "pubKey", "Give me your public key")
        pubKey = serialization.load_pem_public_key(clientsock.recv(8192), default_backend())
        
        print("Got public key from: " + username)
        #print(pubKey)
        self.msg.send_data(clientsock, "sign", "Send Signature")
        print("Got Signature from: " + username)
        signature = clientsock.recv(8192)

        #Calculo da validade da assinatura
        statSign = self.verifySig(pubKey,  signature)

        if statSign: #assinatura e verificação válida
            self.publicKeys[clientsock.getpeername()] = pubKey

            self.msg.send_data(clientsock, "serverKey", "Sending my key")
            print(clientsock.recv(8192))
            clientsock.send(self.pubKey.public_bytes(serialization . Encoding . PEM, serialization.PublicFormat. PKCS1))
            statuscode = clientsock.recv(8192)
            self.msg.send_data(clientsock, "symKey", "Give me symmetric key")
            symKey = clientsock.recv(8192)
            
            print("Got session key from: " + username)
            #print("received chave encriptada " + str(symKey))

            symKey = assymetric_decrypt(self.privKey, symKey)
            self.symetricKeys.append(symKey)

        #Citizen Card
        #self.msg.send_data(clientsock, "signCC", "Send Signature Citizen Card")
        #msgcc = clientsock.recv(8192)
        #if(self.cc_disabler==0):
        #    if(verifySign(getCerts(),username,msgcc)):
        #        print("success!")

        return username
    def verifySig(self, pubKey, sig):
        return verification(pubKey, sig)
        
    def send_data(self,clientsock,action,data):
        info={}
        info["action"]=action
        info["data"]=data
      
        clientsock.send(bytes(json.dumps(info),encoding="utf8"))

    def receive_input(self,connection, max_buffer_size): #input received from the client

        client_input = connection.recv(max_buffer_size) #message recv from client
        client_input_size = sys.getsizeof(client_input)
        if client_input_size > max_buffer_size:
            print("The input size is greater than expected {}".format(client_input_size))
        
        decoded_input = client_input.decode("utf8").rstrip()
        return decoded_input

    def log_in_data(self,username): 
                                       
        if (username in self.d ):
            return False
        else:
            self.d[username]=1
            return True       
       

    def wakeUpLobby(self):

        print("[Server]-I am going to wake up the others")
        for i in range(0,self.logged):
            #print(i)
            self.lobbyLock[i].release()

    def lobby(self):

        print("["+str(self.logged-1)+"]I am going to sleep ")
        self.lobbyLock[self.logged-1].acquire()
