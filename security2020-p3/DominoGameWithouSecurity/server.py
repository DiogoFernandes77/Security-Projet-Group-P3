 
import socket, threading
from waitingRoom import waitingRoom
import sys
from game import Game
from client import *
import random
import pickle
import time
import json
from send_receive import *

def main():
    players_nr=int(input("Choose your number of players in server:"))
    table_manager=ServerTableManager("127.0.0.1",8080,socket.socket(socket.AF_INET, socket.SOCK_STREAM),players_nr)
    table_manager.start_server()
    


class ServerTableManager ():
    
    def __init__(self,localHost,port,server,playersnr):
        self.localHost=localHost
        self.port=port
        self.maxPlayers=playersnr
        self.playersEntering=0
        self.server=server
        self.game=Game(self.maxPlayers)
        self.logged=0
        self.client_ans=""
        self.players={}
        self.msg=msgCommunication()
        self.players_logged=False
        d={'Sergio23': ['abc12312',0], 'Daniel': ['daniel',0],'Gasalho': ['gasalho',0],'Pedro': ['pedro',0],'Dany':['dany',0],
        'bot1': ['bot1',0],'bot2': ['bot2',0],'bot3': ['bot3',0],'bot4': ['bot4',0]}
        self.waitingRoom=waitingRoom(d)

#-----------------SERVER PART 
    #Server initialization 
    def start_server (self):
       
        self.create_socket()
        self.bind_socket()


        server_thread=serverThread(self.waitingRoom,self.game,self.maxPlayers,self.players,self.players_logged,self.playersEntering,self.msg)
        server_thread.start()
        while True:
          #  print("I am waiting for clients")
            self.server.listen(1)
            clientsock, clientAddress = self.server.accept()
            print ("Client at ", clientAddress , " connected...")
            self.playersEntering+=1
            print(self.waitingRoom.logged)
            if self.waitingRoom.logged>=self.maxPlayers:
                self.client_ans=""
                while(self.client_ans!="200-Ok"):
                    self.msg.send_data(clientsock,"PrintQuit","Game is already full ,please try again later  ...")
                    self.client_ans=self.msg.receive_input(clientsock,5120)     
            else:
                self.client_ans=""
                
                while(self.client_ans!="200-Ok"):
                    self.msg.send_data(clientsock,"Print","This is from Server you are ready to play Domino ...")
                    self.client_ans=self.msg.receive_input(clientsock,5120)
 
                self.players.update({clientAddress:[clientsock,0]})
                # self.send_to_player(clientAddress,clientsock)

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
    



class serverThread (threading.Thread):
    
    def __init__(self,waitingRoom,game,players_nr,players,players_logged,playersEntering,msgCommunication):
        threading.Thread.__init__(self)
        self.waitingRoom=waitingRoom
        self.game=game
        self.players=players
        self.current_in_order=0
        self.players_to_logg=0
        self.endgame=False
        self.players_logged=players_logged
        self.players_nr=players_nr #number of players
        self.msg=msgCommunication
        self.gameRegister={}
    
    def run(self):
        temp_dict={}

        while(not self.players_logged):
            if(len(temp_dict)!=len(self.players)):
                temp_dict=self.players.copy()
                for pl in temp_dict:
                    if(temp_dict[pl][1]==0):
                        clSock=temp_dict[pl][0]
                        self.waitingRoom.logging(clSock)
                        temp_dict[pl][1]=1
                        self.players[pl]=temp_dict[pl]

            
            if(self.waitingRoom.logged==self.players_nr):
                self.players_logged=True
        
        self.game.orderList(self.players)
        self.game.printOrderList()
        self.sendPlayerList()
        #------------Tile distribution:
        #socket of firstPlayer
        firstPlayerSock=random.choice(list(self.players.values()))[0]
        self.sendTileDeck(firstPlayerSock)
        #data that contains destiny and tile Deck
        recvDataDest=self.msg.receive_inputDest(firstPlayerSock)
        destSock=self.getPlayerSock(recvDataDest[0])
       
        while (recvDataDest[1]!=[]):
            self.msg.send_data(destSock,"sendTileDeck",recvDataDest[1])
            print(destSock.recv(5120).decode()+" from "+str(recvDataDest[0])) # 200-0K from client
            recvDataDest=self.msg.receive_inputDest(destSock)
            destSock=self.getPlayerSock(recvDataDest[0])
        
        #end of tiles distritbution
        while (not self.game.gameEnded):
            clientSock=self.game.order_list[self.current_in_order][1]
            clientAddr=self.game.order_list[self.current_in_order][0]
            player_moves=list()
            cheater_flag,tupleChoice=self.game.myTurn(clientSock,self.current_in_order)
            print("Cliente answer:"+str(tupleChoice))
            if(cheater_flag):
                suspicious_players=list()
                suspicious_players.append(clientAddr)
                for tile_played in tupleChoice:
                    print(tile_played)
                    tile=domino(tile_played["data"]["bottom"],tile_played["data"]["top"])
                    print(tile)
                    second_cheater=self.get_secondCheater(tile,clientAddr)
                    suspicious_players.append(second_cheater)
                    self.ask_secondCommit(suspicious_players)
                break
            else:
                #check if clientAddr is in the register 
                if(clientAddr in self.gameRegister.keys()):
                    player_moves=list(self.gameRegister[clientAddr])
                    player_moves.append(tupleChoice)
                    self.gameRegister.update({clientAddr:player_moves})
                #empty list 
                else:
                    player_moves.append(tupleChoice)
                    self.gameRegister.update({clientAddr:player_moves})
                self.controlNextPlayer()
                #check for cheaters ( repeated tiles in board)
                flag,tile=self.checkCheaters(self.game.domino_tableboard.board)
                if(flag):
                    suspicious_players=list()
                    suspicious_players.append(clientAddr)
                    tile=self.checkCheaters(self.game.domino_tableboard.board)[1]
                    second_cheater=self.get_secondCheater(tile,clientAddr)
                    #this is just to guarantee that the same player has played twice a tile 
                    if(second_cheater!=None):
                        #print("First cheater is "+ str(clientAddr))
                        #print("Second cheater is "+str(second_cheater))
                        suspicious_players.append(second_cheater)
                    #ask for second commit 
                    self.ask_secondCommit(suspicious_players)
                    break

        #gameRegister
        #print(self.gameRegister)
        self.gameisOver()

    def controlNextPlayer(self):
        
        self.game.printOrderList()
        if(not self.game.checkPlayerFlag(self.current_in_order)): #Player is not /choosing
            if(self.current_in_order==3):
                self.current_in_order=0
            else:
                self.current_in_order+=1
   
    #tell the players that the game is Over!!
    def gameisOver(self):

        for i in range(0,self.players_nr):
            clSock= self.game.order_list[self.current_in_order][1]
            self.msg.send_data(clSock,"GetPlayerPoints","points",)

            self.msg.send_data(clSock,"Quit","Quit!",)
            self.controlNextPlayer()
    
    #send the list of players for each player 
    def sendPlayerList(self):
        
        for player in self.players:
            clSock=self.players[player][0] #clientSocket
            self.msg.send_data(clSock,"sendPlayersList",self.getPlayerAddrList())

    #returns a list with players addr
    def getPlayerAddrList(self):
        playerAddrList=list()
        for player in self.players:
            playerAddrList.append(player)
        
        return  playerAddrList

    #send tile deck to the respective clSock 
    def sendTileDeck(self,clSock):
        self.msg.send_data(clSock,"sendTileDeck",self.game.domino_tableboard.domino_tilesJSON) #sendDominoTiles to player
        print(self.msg.receive_input(clSock,1024))
    
    # returns socket giving the adress
    def getPlayerSock(self,clAddr):
        
        for addr in self.players:
            #print("Addr="+str(addr)+"=="+ str(clAddr) +"ClAddr")
            if(addr[1]==clAddr[1]):
                #print(self.players[addr][0])
                return self.players[addr][0]

    #checks if there are repeated tiles in table 
    def checkCheaters(self,boardTiles):
        print("Checking for cheaters!!")
        cheater_flag=False
        cheater_tile=""
        
        for i in range(0,len(boardTiles)):
            tile=boardTiles[i]
            #converts to domino just to facilitate the comparison
            domino_tile=domino(tile['data']['bottom'],tile['data']['top'])
            for j in range(i+1,len(boardTiles)):
                rep_tile=boardTiles[j]
                domino_reptile=domino(rep_tile['data']['bottom'],rep_tile['data']['top'])

                print("Rep tile:"+ str(domino_reptile) + "== " +str(domino_tile) + " :Tile")
                if(domino_tile.equalTile(domino_reptile)):
                    print("CHEATER CAUGHT!!")
                    cheater_flag=True
                    cheater_tile=domino_tile
                    return cheater_flag,cheater_tile
    
        return cheater_flag ,cheater_tile
    
    #cheater was caught!
    #check who played repeated tiles
    #
    def get_secondCheater(self,tile,firstCheater):
        
        print("Repeated tile is " + str(tile))
        for d in self.gameRegister.values():
            playersAddr=list(self.gameRegister.keys())
            player_moves=list(self.gameRegister.values())
            #converts to domino just to facilitate the comparison
            for plays in d:
                #print("PLAYS=")
                #print(plays)
                if(plays[0]["index"]!=-1): #discard invalid moves
                    domino_tile=domino(plays[0]["data"]["bottom"],plays[0]["data"]["top"])
                    if(domino_tile.equalTile(tile)):
                        position=player_moves.index(d)
                        clientAddr=playersAddr[position]
                        print("ClientAddr is ="+str(clientAddr))
                        if(clientAddr!=firstCheater):
                            return clientAddr
                            

    
    def ask_secondCommit(self,listCheaters):
        print("Cheaters list is")
        print(listCheaters)
        #if(len(listCheaters))
        for addr in listCheaters:
            clientSock=self.getPlayerSock(addr)
            self.msg.send_data(clientSock,"secondCommit","secondCommit")
            print(self.msg.receive_input(clientSock,2048))

if __name__ == "__main__":
   main()

