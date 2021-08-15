import json
import sys
import pickle

class msgCommunication:
    
    def _init_(self):
        print("Ola")

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
        #result = process_username(decoded_input)
        return decoded_input

    #client sends data to server with the respective destiny
    def send_data_dest(self,clientsock,destiny,data):
        info={}
        info["destiny"]=destiny
        info["data"]=data
        # print("Sending stuf...")
        #print(data)
        clientsock.send(bytes(json.dumps(info),encoding="utf8"))        

    def receive_inputDest(self,clientsock):
        # print("Receiving some stuff...")
        clientmsg=json.loads(clientsock.recv(5120).decode())
        destiny=clientmsg["destiny"]
        data=clientmsg["data"]
        
        return destiny,data
