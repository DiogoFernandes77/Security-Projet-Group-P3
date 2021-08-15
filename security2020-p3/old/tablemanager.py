 
import socket, threading
from waitingRoom import waitingRoom
import sys
from game import Game
import random
import pickle
import time

def main():

    players_nr=int(input("Choose your number of players in server:"))
    table_manager=ServerTableManager("127.0.0.1",8000,socket.socket(socket.AF_INET, socket.SOCK_STREAM),players_nr)
    table_manager.start_server()
    


class ServerTableManager ():
    
    def __init__(self,localHost,port,server,playersnr):
        self.localHost=localHost
        self.port=port
        self.players_nr=playersnr
        self.server=server
        self.game=Game(self.players_nr)
        self.logged=0
        self.threads=list()

        d={'Sergio23': ['abc12312',0], 'Daniel': ['daniel',0],'Gasalho': ['gasalho',0],'Pedro': ['pedro',0],'Dany':['dany',0]}
        self.waitingRoom=waitingRoom(d,self.logged)

#-----------------SERVER PART 
    #Server initialization 
    def start_server (self):
       
        #THREADS MUST BE HERE
        self.create_socket()
        self.bind_socket()

        #server thread initialization
        server_thread=serverThread(self.waitingRoom,self.game,self.threads)
        server_thread.start()
        thread_id=0
        while True:
            self.server.listen(1)
            clientsock, clientAddress = self.server.accept()
            print(clientAddress)
            print ("Client at ", clientAddress , " connected...")
            if self.waitingRoom.logged>self.players_nr:
                clientsock.send(bytes("(ERROR)\tGame is already full ,please try again later  ...",'utf-8'))
         
            else:
                clientsock.send(bytes("(PRINT)\tHi, This is from Server you are ready to play Domino ...",'utf-8'))
                newthread=playerThread(clientAddress,clientsock,self.waitingRoom,self.game,thread_id)
                newthread.start()
                thread_id+=1
                self.threads.append(newthread)

   


#create socket          
    def create_socket(self):
        
        try:
            self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg: 
            print("socket creation error:" + str(msg))

    #bind socket
    def bind_socket(self):
        
        try:
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.localHost, self.port))
            
            print("Server started")
            print("Waiting for client request..")
        
        except socket.error as msg:
            print("socket binding error:" + str(msg))
            self.bind_socket()
    
class playerThread (threading.Thread):
    
    def __init__(self,clAddr,clSock,waitingRoom,game,thread_id):
        threading.Thread.__init__(self)
        self.clAddr=clAddr
        self.clSock=clSock
        self.waitingRoom=waitingRoom
        self.game=game
        self.hand=list()
        self.thread_id=thread_id

    def run(self):
        #server thread
        
        self.waitingRoom.logging(self.clSock,self.clAddr)
        self.waitingRoom.lobby()
        # to test hand distribution comment this part 
        self.hand=self.game.sendHand(self.clAddr,self.thread_id)
    
        #APENAS PARA FASE INICIAL EM QUE É OBRIGATORIO TODOS OS 4 JOGADORES TEREM 7 PEÇAS
        #To test this uncomment this part 

        # while(not len(self.hand)==7):
        #     self.hand=self.game.chooseTile(self.clSock,self.thread_id,self.hand)
        #     time.sleep(1)
        #COMMIT HAND HERE !!!!!!! 

        while( not self.game.gameEnded):
            self.hand=self.game.myTurn(self.clSock,self.thread_id,self.hand)
            time.sleep(1)



class serverThread (threading.Thread):
    
    def __init__(self,waitingRoom,game,threads):
        threading.Thread.__init__(self)
        self.waitingRoom=waitingRoom
        self.game=game
        self.threads=threads
        self.current_in_order=0
        self.endgame=False
    
    def run(self):

        while(self.waitingRoom.logged!=4):
            time.sleep(1)
            print("[Server]Waiting for other users")
        
        self.waitingRoom.wakeUpLobby()
        self.game.piece_distributor(self.threads)
        self.game.sleepPlayers()
        self.game.orderList(self.threads)
        self.game.printOrderList()

        self.game.wakeUpPlayer(self.game.order_list[self.current_in_order][0].thread_id)    
        self.game.order_list[self.current_in_order][1]=1 #order is the same for playing and for choosing 
       
        # while self.game.domino_tableboard.domino_tiles!=[]:
        #     self.controlNextPlayer()
        
        # #NAO ESTA A MUDAR DE JOGADOR !!!!
        # self.game.sleepPlayers()

        # self.game.wakeUpPlayer(self.game.order_list[self.current_in_order][0].thread_id)    
        # self.game.order_list[self.current_in_order][1]=1 #order is the same for playing and for choosing 
        
        while(not self.game.gameEnded):
            self.controlNextPlayer()
          

        #     self.game.printOrderList()
        #     time.sleep(1)
        #     if(not self.game.checkPlayerFlag(self.current_in_order)): #Player is not Playing
        #         self.game.printOrderList()

        #         if(self.current_in_order==3):
        #             self.current_in_order=0
        #         else:
        #             self.current_in_order+=1
        #         self.game.nextPlayerTurn(self.current_in_order)

    def controlNextPlayer(self):
        
        self.game.printOrderList()
        time.sleep(1)
        if(not self.game.checkPlayerFlag(self.current_in_order)): #Player is not /choosing
            if(self.current_in_order==3):
                self.current_in_order=0
            else:
                self.current_in_order+=1
            
            self.game.nextPlayerTurn(self.current_in_order)


if __name__ == "__main__":
   main()

