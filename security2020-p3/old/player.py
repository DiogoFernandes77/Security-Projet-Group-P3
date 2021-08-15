import socket, threading
import sys
import time 
import json
import pickle
from math import *



class Player:
    
    
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 8000
        self.addr = (self.host, self.port)
        self.state=1
        self.server_msg=""
        self.connect()
        self.player_hand=list()
 
     

    def connect(self):
        try:
            self.s.connect(self.addr) 
            #return self.s.recv(2048).decode() #return ID
        except:
            "Error connecting to the server!"


    def send_data(self, data):
        try:
            self.s.send(str.encode(data))
            #return self.s.recv(2048).decode()
        except socket.error as e:
            print(e)
                                                #Player states: #1-> waiting for logIn
                                                                #2-> Logging...
                                                                #3->In lobby
                                                                #4->Playing 
                                                                #0->Exiting
    #print data from server 
    def printServer(self):
        #global state        

        txt=self.server_msg.split('\t')
        
        if(txt[0]!="(PRINT)"):
           return False
        else:
            print(txt[1])
            self.send_data('-')
            return True
            
    def logging(self):
        
        self.server_msg=self.s.recv(1024).decode("utf8")
        if(self.server_msg=="password:" or self.server_msg=="\nUsername:"):
            while self.server_msg!= "Logged In ":
                message=input(self.server_msg)
                self.send_data(message)
                self.server_msg=self.s.recv(1024).decode("utf8")

        #self.send_data("Waiting")

    def run_tasks(self):

        while(self.state!=0):
            if(self.state==1): #printing some stuff
                self.server_msg=self.s.recv(4096).decode("utf8")
                if(self.printServer()):
                    self.state=2
                else:
                    self.state=0

            elif(self.state==2):
                self.logging()
                self.state=3

            elif(self.state==3): #lobby waiting
                print("Waiting in lobby ...")
                self.state=4
            elif(self.state==4):
                self.recieveTiles(self.s.recv(4096))
                self.send_data("200")
                self.state=5

            elif(self.state==5):
                
                self.server_msg=self.s.recv(4096).decode("utf8")
                if (not self.printServer()): 
                    message=input(self.server_msg)
                    self.send_data(message)
                    self.state=5
                else:
                    self.send_data("200")
                    self.state=4
        
    def recieveTiles(self,data):
        player_tiles=list()
        
        try:
           player_tiles=pickle.loads(data).copy()
        except:
            print("Failed to load")
        
        self.printTiles(player_tiles)

    
    def printTiles(self,data):
        hand='['
        for d in data:
            hand+=str(d) + ','
            
        hand+=']'
        print(hand)


        
  

def main():
    p=Player()
    p.run_tasks()


    

if __name__ == "__main__":
   main()


