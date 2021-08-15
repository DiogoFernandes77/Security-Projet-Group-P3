import socket, threading
import sys
import time 
import json
import pickle
import random
from math import *
from domino import *
from send_receive import *

class Player:
    
    def __init__(self,playerType,maximProbCheater):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 8080
        self.addr = (self.host, self.port)
        self.server_msg=""
        self.player_hand=list()
        self.action=""
        self.data=""
        self.board=list()
        self.playerType=playerType # player type can be : (0)bot or human (1)
                                #this should be in args
                                #Ex: client.py 0 or client.py 1 
        self.botsLogin=["bot1","bot2","bot3","bot4"]
        self.connect()
        self.msgtoClient=msgCommunication()
        self.playersList={}
        self.tilePlayed = None
        self.botCount=0
        
        self.deck_to_cheat=self.readTilesinFile()
        self.points=0
        self.maximProbCheater=maximProbCheater
        

    #connection to the server 
    def connect(self):
        try:
            self.s.connect(self.addr) 
        except:
            "Error connecting to the server!"
    #send_data to server
    def send_data(self, data):
       
        try:
            self.s.send(data.encode("utf8"))
            #return self.s.recv(2048).decode()
        except socket.error as e:
            print(e)

    
    def run_tasks(self):
        cheater_move=list()
        while(self.action!="Quit"):
            self.updateServerMsg() #this update is only to get the Action and data
            print("player hand = ")
            print(self.player_hand)
            if self.action=="Print":
                self.printServer()
            elif self.action=="PrintQuit":
                self.printServer()
                break
            elif(self.action=="Auth"):
                if(self.data=="Logged Sucessufully"):
                    print("Waiting in Lobby...")
                    self.send_data("200-Ok")
                else:   
                    self.logging()

            elif(self.action=="sendTileDeck"):
                deckTiles=self.recieveTiles()
                self.send_data("200-Ok")
                tiledeck=self.choosingTile(deckTiles)
                #self.randomNextPlayer()
                #print(tiledeck)
                self.msgtoClient.send_data_dest(self.s,self.randomNextPlayer(),tiledeck)
            
            elif(self.action=="sendPlayersList"):
                self.playersList=self.data 
                print(self.playersList)
       
            elif(self.action=="SendTile"):
                self.printTiles(self.player_hand,"player_hand")
                flag,cheater_moves=self.checkForCheaters()
                if(flag):
                    self.send_data("Cheater caught!")
                else:    
                    self.sendTile()
            
            elif(self.action=="Send suspicious moves"):
                self.s.send(bytes(json.dumps(cheater_moves),encoding="utf8"))

            elif(self.action=="PrintBoard"):
                print("--------------------Board-------------------------")
                self.board=self.data
                self.printTiles(self.board,"board")
                print("--------------------------------------------------")
                self.send_data("200-Ok")

            #elif(self.action=="TileDir"):
             #   self.chooseTileDir()
            
         #   elif(self.action=="BoardLocation"):
          #      self.chooseBoardLocation()

            elif(self.action=="RemoveTile"):
                
                self.removeHandTile()
            
            elif(self.action=="CheckifEmpty"):
                self.checkifHandisEmpty()
            
            elif(self.action=="secondCommit"):
                print("Sending my secondCommit")
                self.send_data("200-Ok")

            elif(self.action=="GetPlayerPoints"):
                self.getPlayerPoints()


    #print data from server 
    def printServer(self):
        print(self.data)
        self.send_data("200-Ok")
        
    def logging(self): 
        
        if(self.data=="password:" or self.data=="\nUsername:"):
            if(self.checkBotHuman()):#human
                message=input(self.data)
            else:#bot
                message=self.botLogin()  
                if(self.data=="password:"):
                    if(self.botCount==3):
                        self.botCount=0
                    else:
                        self.botCount+=1
            self.send_data(message)
       
    def choosingTile(self,deckTiles): 

        tmpdeckTiles=deckTiles.copy()
        # player must have less than 7 tiles and boarTiles shouldn't be empty
        if (len(self.player_hand)<7 and deckTiles!=[]):
            prob=random.randint(0,100)
            if(prob<=5):
                print("ChooseTile(y/n)?",end='')
                chooseTile="y"
            else:
                chooseTile="n"
            
            print("Prob= " + str(prob) + " answer="+chooseTile)

            # if user wants to choose tile 
            # user can cheat but in this case we are just trying to 
            # make sure that the user chooses a valid tile from board
            # ADD SOME STUFF HERE TO MAKE POSSIBLE USER TO CHEAT ( IN THE END )
            
            if(chooseTile=='y'):
                #print("Choose tile idx:",end='')
                tileidx=random.randint(0,len(tmpdeckTiles)-1)
                print(str(tileidx))
                tile=tmpdeckTiles[int(tileidx)]
                print("Tile choosed is "+str(tile))
                tmpdeckTiles.remove(tile)
                
                self.player_hand.append(tile)
            
            #user don't want to choose tile
            # two options:
            #do nothing
            # exchange tile 
            #here prob is 50/50 (do nothing or exchange tile)
            else:
                if(self.player_hand!=[]):
                    changeTile="y"
                    while(changeTile=="y"):
                        print("Do you want to exchange a tile(y/n)?",end='')
                        changeTile=random.choice(["y","n"])
                        print(changeTile)
                        if(changeTile=='y'):
                            print("Your hand is ->",end='')
                            self.printTiles(self.player_hand,"others")
                            #print("Choose tile idx of your hand you want to exchange:",end='')
                            tileidx=random.randint(0,len(self.player_hand)-1)
                            print("Index choosed:"+str(tileidx))
                            tmpTile=self.player_hand[int(tileidx)]
                            
                            print("You choosed"+str(self.jsonToDomino(tmpTile)))
                            #print("Choose board tile idx you want to exchange:",end='')
                            boardtileidx=random.randint(0,len(tmpdeckTiles)-1)
                            print("Board index choosed:"+str(boardtileidx))
                            boardTile=tmpdeckTiles[int(boardtileidx)]
                            print("Board tile choosed is "+str(self.jsonToDomino(boardTile)))
                            tmpdeckTiles[int(boardtileidx)]=tmpTile
                            self.player_hand[int(tileidx)]=boardTile


        print("Deck tiles to send:")
        random.shuffle(tmpdeckTiles)
        self.printTiles(tmpdeckTiles,"other")    
        print("\n")                
        return tmpdeckTiles

    def updateServerMsg(self):
        #print(msg_server)
       
        self.server_msg=json.loads(self.s.recv(8192).decode())
        self.action=self.server_msg["action"]
        self.data=self.server_msg["data"]
       
    def recieveTiles(self):
        deckTiles=list()
        try:
           deckTiles=self.data.copy()
        except:
            print("Failed to load")
        
        #print(deckTiles)
        #tiles=self.jsonListToDomino(deckTiles)
        print("Deck Tiles:")
        self.printTiles(deckTiles,"other")
        return deckTiles

    def sendTile(self):
        print(self.data,end='')
        null={}
        null['index']=-1
        null['data']=0
        tile=(null,0,0)
        

        if(self.checkBotHuman()):#human
            idx=-1
            while( idx<= len(self.player_hand)):
                idx=input("Choose an idx of your hand")
            tileChoice=self.player_hand[idx]
            invertTile=-1
            while(invertTile!=0 and invertTile!=1):
                invertTile=input("Invert tyle(0/1)?")
            chooseTile='a'
            while(chooseTile!='l' or chooseTile!='r'):
                chooseTile=input("BoardLocation(l/r)?")
                
            tile=(tileChoice,invertTile,chooseTile)
            #ESTA PARTE TEM Q SER MELHORADA !!!
        else:
            #idx=random.randint(0,len(self.player_hand)-1)
            
            possible_choices=self.chooseBestTileToPlay()
            #print(idx)
            if(possible_choices!=[]):
                tile=random.choice(possible_choices)

        print("\nYou choosed "+str(tile))
       # print(tile[0]['data'])
        if (tile[0]['data']!=0):
            self.tilePlayed=tile[0] 

        self.send_data(json.dumps(tile))
    
    #can only detect one kind of cheater  
    # if someone played a tile that belongs to him 
    def checkForCheaters(self):

        print("\nChecking for cheaters...")
        
        #print(self.board)
        #print(self.player_hand)
        cheater_caught=False
    
        #list that contains repeated moves 
        cheaters_moves=list()
        for tile in self.board:
            #converts to domino
            domino_tile=domino(tile["data"]["bottom"],tile["data"]["top"])
            #print(domino_tile)

            #checks if board tile is in their hand
            playerHandDomino=self.jsonListToDomino(self.player_hand,True)
            for d in playerHandDomino:
                #print("My hand tiles:"+str(d))
                if(d.equalTile(domino_tile)):
                    print("\nCheater caught!!!!!")
                    #print("My hand is:")
                    self.printTiles(self.player_hand,"player_hand")

                    cheater_caught=True
                    if tile not in cheaters_moves:
                        cheaters_moves.append(tile)
            
        return cheater_caught,cheaters_moves
                    

    def chooseBestTileToPlay(self):
        possible_choices=[]
        cheat_prob=random.randint(0,100)
        print("\nProbability to cheat=" + str(cheat_prob))
        if(self.board!=[]):
            #probability to cheat
            begin=self.jsonToDomino(self.board[0])
            end=self.jsonToDomino(self.board[-1])
            #plays with the all deck 
            if(cheat_prob<=self.maximProbCheater):
                possible_choices=self.playTile(begin,end,self.deck_to_cheat)
            #plays only with his deck
            else:
                possible_choices=self.playTile(begin,end,self.player_hand)


        else:
            #if board is empty player should choose a random tile ,random direction(this is optional),random invertion ( inverted or not )
            possible_choices.append((self.player_hand[random.randint(0,len(self.player_hand)-1)],random.choice(["l","r"]),random.choice([0,1])))
        return possible_choices
    
    def playTile(self,begin,end,deck_hand):
        possible_choices=[]

        for data in deck_hand:
            d=self.jsonToDomino(data)
            i=data['index']
            if(d.top==end.bottom):
                possible_choices.append((data,'r',0))
            if(d.bottom==begin.top):
                possible_choices.append((data,'l',0))
            inverted_d=d
            inverted_d.invertTile()
            if(inverted_d.top==end.bottom):
                possible_choices.append((data,'r',1))
            if(inverted_d.bottom==begin.top):
                possible_choices.append((data,'l',1))
        return possible_choices
    
    def removeHandTile(self):
        print(self.tilePlayed)
        if(self.tilePlayed in self.player_hand):
            self.player_hand.remove(self.tilePlayed)
    

    #choose a random player from the list 
    def randomNextPlayer(self):
        flag=True 
        playerAddr=""
        while(flag):
            playerAddr=random.choice(self.playersList)
            if(playerAddr[1]!=self.s.getsockname()[1]):# checks if random doesn't selects its own addr
                flag=False

        return playerAddr

    def chooseBoardLocation(self):
        print(self.data,end='')
        if(self.checkBotHuman()):#human
            message=input()
            self.send_data(message)        
        else:
            message=random.choice(['l','r'])
            self.send_data(str(message)) 
            print(message)
   
    #choose tile direction
    def chooseTileDir(self):
        
        print(self.data,end='')
        if(self.checkBotHuman()):#human
            message=input()
            self.send_data(message)        
        else:
            message=random.choice([0,1])
            self.send_data(str(message)) 
            print(message)


    def printTiles(self,data,printType):
        #if printType="board" should not include "count"
        count=0
        hand='['
        for d in data:
            if(printType=="board"):
                hand+=str(self.jsonToDomino(d)) + ' | ' 
            else:
                hand+=str(count)+ ":"+str(self.jsonToDomino(d)) + ' | ' 
                count+=1
        hand+=']'
        print(hand)

    def jsonListToDomino(self,tiles,index=None):
        new_data=list()
        if (len(tiles)>0):
            for d in tiles:
                if(index==None):
                    tile=(d['index'],domino(d['data']['bottom'],d['data']['top']))
                #print(tile)
                else:#list of dominos
                    tile=domino(d['data']['bottom'],d['data']['top'])

                new_data.append(tile)
        
        return new_data
    
    def checkBotHuman(self): #returns True if Human else returns False
        if(self.playerType==1):
            return True
        else:
            return False

    def jsonToDomino(self,tile):
        return (domino(tile['data']['bottom'],tile['data']['top']))

    def botLogin(self): 
        print(self.botsLogin[self.botCount])
        return self.botsLogin[self.botCount]

    def checkifHandisEmpty(self):
        if(len(self.player_hand)==0):
            self.send_data("True")
        else:
            self.send_data("False")

    def getPlayerPoints(self):
        for data in self.player_hand:
            tile=self.jsonToDomino(data)
            tilepoints = tile.getBottom()+tile.getTop()
            self.points+=tilepoints
        print("Player had :"+ str(self.points))


    def readTilesinFile(self):
        f=open("dominoTiles.txt","r")
        domino_tiles=[]
        while(f.readline()):
            domino_tiles.append(json.loads(f.readline()))
            #f.read(json.loads(data))
            #f.write("\n")
        
        #print(domino_tiles)
        f.close()
        return domino_tiles

        
def main():
    
    try:
        print(sys.argv[1])
        print(sys.argv[2])
    except:
        print("Please enter:\n[arg1]->type of player: [0]-bot \t[1]-human  \n[arg2]->cheater maxim probability: 0-100")
        exit(1)

    player_type=int(sys.argv[1])
    maximProbCheater=int(sys.argv[2])
    if(player_type!=0 and player_type!=1):
        print("Type of player '" +str(player_type)+"' is invalid please try again [arg1]:\n0-bot \n1-human \n ")
    elif(maximProbCheater<0 or maximProbCheater>100):
        print("Probability '" +str(maximProbCheater)+"' is invalid please try again [arg2]:cheater Maxim porbability ( 0-100)\n")

    else:
        p=Player(player_type,maximProbCheater)
        p.run_tasks()



    

if __name__ == "__main__":
   main()