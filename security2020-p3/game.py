
import  random
from domino import *
import json
import threading
import pickle
import time
from table import Table
import sys
from send_receive import *

class Game():
    def __init__(self,players):

        self.domino_tableboard = Table()
        self.players=players
        self.order_list={}
        self.playingFlag=False 
        self.gameEnded=False #game ended
        self.gameRegister=list()
        self.msgComm=msgCommunication()
        self.noMoreValidTiles={}


    
    def orderList(self,players_list):
        pl=players_list.copy()
        count=0
        while len(pl)>0:
            player=random.choice(list(pl.keys()))
            self.order_list.update({count:[player,pl[player][0],0]})
            del pl[player]
            count+=1

    def myTurn(self,clientAddr,username,clSock,currentIdx,stock):
        
        turn = True    
        cheater_flag=False 
        tupleChoice=""
        has_tile = True
        #if player played a Tile or not 
        playedTile=False

        self.order_list[currentIdx][2]=1 #player starting 

        tileidx=-1
        tile_dir=-1
        tile_place=""
        #sending game register
        if(self.gameRegister!=[]):
            self.msgComm.send_data(clSock,"GameRegister",str(self.gameRegister))
            print(self.msgComm.receive_input(clSock,5120))
        #sending board 
        self.msgComm.send_data(clSock,"PrintBoard",self.domino_tableboard.board)
        print(self.msgComm.receive_input(clSock,5120))
        #Asking player for a tile
        self.msgComm.send_data(clSock,"SendTile","Choose a tile you want to play:")
        playerAns=self.msgComm.receive_input(clSock,5120)
        print("playerAns==" + str(playerAns))
        
        if(playerAns=="Cheater caught!"):
            self.msgComm.send_data(clSock,"Send suspicious moves","Send your suspicious moves")
            tupleChoice=json.loads(self.msgComm.receive_input(clSock,5120))
            print(tupleChoice)
            turn = False
            cheater_flag=True    

        else:
            tupleChoice=json.loads(playerAns)

            #player have a  tile to play
        # print(tupleChoice)
            if(tupleChoice[0]['data']!=0):
                #print("enter here")
                tileJson,tile_place,tile_dir=tupleChoice
                tile=self.jsonToDomino(tileJson)

                if(int(tile_dir)==1):
                    tile.invertTile()
                    print("Tile inverted is " + str(tile))           
                tileTuple={}
                tileTuple['index']=tileJson['index']
                tileTuple['data']=tile.data
                if(self.domino_tableboard.isValidPlay(tile_place,tileTuple)):
                    if(tile_place=="r"):
                        self.domino_tableboard.board.append(tileTuple)

                    else:
                        self.domino_tableboard.board.insert(0,tileTuple)
                    
                    self.gameRegister.append({(clientAddr,username):(tileJson,tile_place,tile_dir)})
                    turn = False
                    playedTile=True

                    self.msgComm.send_data(clSock,"RemoveTile","Yes")
                    print(self.msgComm.receive_input(clSock,5120))
                    
                #not valid tile 
                else:
                    self.msgComm.send_data(clSock,"Print","This is not a valid play, please try again!")
                    print(self.msgComm.receive_input(clSock,5120))
                    #turn = True

        
        #player doesn't have a valid tile to play
            else:
                if stock != []:
                    has_tile = False
                else:
                    self.noMoreValidTiles.update({clSock:True})
                        
            self.checkifEndGame(clSock)
            

        self.order_list[currentIdx][2]=0 #player finished 
        return cheater_flag,tupleChoice, has_tile,playedTile


    def checkifEndGame(self,clSock):
        if(len(self.domino_tableboard.board)==28):
            self.gameEnded=True 
        self.msgComm.send_data(clSock,"CheckifEmpty","check")

        if(all(value == True for value in self.noMoreValidTiles.values()) and len(self.order_list)==len(self.noMoreValidTiles)):
            self.gameEnded=True

        checkEmpty = self.msgComm.receive_input(clSock,5120)
        print(checkEmpty)
        if(checkEmpty=="True"):
            self.gameEnded=True 
        
     
    #Check if Player is playing    
    def checkPlayerFlag(self,currentPlayer):
           
        if(self.order_list[currentPlayer][2]==1):#means that the player th is playing 
            return True
        else:
            return False
    

    def jsonToDomino(self,tileJson):
        return domino(tileJson['data']['bottom'],tileJson['data']['top'])
   
    def printOrderList(self):
        print("Order is:")
        for index in self.order_list:
            clAddr=self.order_list[index][0]
            clSock=self.order_list[index][1]
            flag=self.order_list[index][2]
            print("\nclAddr="+str(clAddr) + "\tclSock="+str(clSock) +  "\tFlag="+str(flag))



        

