

import threading
import sys
import json

class waitingRoom():

    def __init__(self,d):
        self.d = d
        self.lobbyLock=list()
        self.logged=0
     
    def logging(self,clientsock):

        username=""
        password=""
        loggIn=self.log_in_data(username,password)
        #while (True,1) or (False)
        while((loggIn[0] and  loggIn[1]==1)) or not loggIn[0]: #LOGIN
            print("Asking for username")
            self.send_data(clientsock,"Auth","\nUsername:" )
            username = self.receive_input(clientsock, 1024) 
            print(username)

            print("Asking for password")
            self.send_data(clientsock,"Auth","password:")
            password = self.receive_input(clientsock, 1024)
            print(password)
            loggIn=self.log_in_data(username,password)
            print(loggIn)
            if (not loggIn[0]):#False
                if loggIn[1] ==-1 :
                    #clSock.send(bytes("Incorrect username please try again...",'utf-8'))
                    self.send_data(clientsock,"Print","Incorrect username please try again...")
                    print(self.receive_input(clientsock, 1024))
                else:
                    self.send_data(clientsock,"Print","Incorrect password  please try again...")
                    print(self.receive_input(clientsock, 1024))

            else:#True
                if(loggIn[1]==1):
                    self.send_data(clientsock,"Print","User is already logged ......")
                    print(self.receive_input(clientsock, 1024))

                else:
                    print("User logged  as " + username)
                    self.logged+=1
                    self.send_data(clientsock,"Auth","Logged Sucessufully")
                    print(self.receive_input(clientsock, 1024))

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

    def log_in_data(self,username,password): 
                                        #Users/password in the system 
                                        #0 -> means it's not logged
                                        #1 -> means it's logged
                                        #-1 -> means username does not exist
                                        #-2 -> means incorrect password
        if (username in self.d ):
            if(self.d.get(username)[0]==password):
                if(self.d.get(username)[1]==0):
                    self.d[username][1]=1
                    return True,0
                else:
                    return True,1 #User already logged        
            else:
                return False,-2 #incorrect password 
        else :
            return False,-1 #incorrect username

    def wakeUpLobby(self):

        print("[Server]-I am going to wake up the others")
        for i in range(0,self.logged):
            #print(i)
            self.lobbyLock[i].release()

    def lobby(self):

        print("["+str(self.logged-1)+"]I am going to sleep ")
        self.lobbyLock[self.logged-1].acquire()
