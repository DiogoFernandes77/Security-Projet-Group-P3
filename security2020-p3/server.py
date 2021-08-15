 
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
from cryptoAssym import *
from bit_commitment import *

def main():
    players_nr = -1
    while(players_nr< 2 or players_nr > 4):
        players_nr=int(input("Choose your number of players in server:"))
        
    playAgain=""
    while(playAgain!="n"):
        table_manager=ServerTableManager("127.0.0.1",8000,socket.socket(socket.AF_INET, socket.SOCK_STREAM),players_nr)
        table_manager.start_server()
        playAgain=""
        while(playAgain!="n" and playAgain!="y" ):
            playAgain=input("Do you want to open table again?(y/n):")

    


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
       # d={'Sergio23': ['abc12312',0], 'Daniel': ['daniel',0],'Gasalho': ['gasalho',0],'Pedro': ['pedro',0],'Dany':['dany',0],
       # 'bot1': ['bot1',0],'bot2': ['bot2',0],'bot3': ['bot3',0],'bot4': ['bot4',0]}

        self.privKey = assymetric_key_generator()
        
        self.pubKey  = self.privKey.public_key()
        
        self.waitingRoom=waitingRoom( self.privKey, self.pubKey)
        
       

#-----------------SERVER PART 
    #Server initialization 
    def start_server (self):
       
        self.create_socket()
        self.bind_socket()


        server_thread=serverThread(self.waitingRoom,self.game,self.maxPlayers,self.players,self.players_logged,self.playersEntering,self.msg, self.privKey, self.pubKey)
        server_thread.start()
        
        while self.waitingRoom.logged!=self.maxPlayers-1:
          #  print("I am waiting for clients")
            self.server.listen(1)
            
            clientsock, clientAddress = self.server.accept()
            print ("Client at ", clientAddress , " connected...")
            self.playersEntering+=1
            print(self.waitingRoom.logged)
            if self.waitingRoom.logged>=self.maxPlayers:
                self.client_ans=""
                if(self.client_ans!="200-Ok"):
                    self.msg.send_data(clientsock,"PrintQuit","Game is already full ,please try again later  ...")
                    self.client_ans=self.msg.receive_input(clientsock,5120)     
            else:
                self.client_ans=""
                
                while(self.client_ans!="200-Ok"):
                    self.msg.send_data(clientsock,"Print","This is from Server you are ready to play Domino ...")
                    self.client_ans=self.msg.receive_input(clientsock,5120)
 
                self.players.update({clientAddress:[clientsock,0]})
        
        server_thread.join()

        
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
    
    def __init__(self,waitingRoom,game,players_nr,players,players_logged,playersEntering,msgCommunication,privkey,pubkey):
        threading.Thread.__init__(self)
        self.waitingRoom=waitingRoom
        self.game=game
        self.players=players
        self.current_in_order=0
        self.endgame=False
        self.players_logged=players_logged
        self.players_nr=players_nr #number of players
        self.msg=msgCommunication
        self.privKey = privkey
        self.pubKey = pubkey
        self.randomization_order = []
        self.playersCommit={}# addres:commit[1] , commit[2]
        self.de_anonymizationPubKey = {}
        self.reveal_map_by_order = list()
        #Citizen Card
        self.cc_disabler = 1
        self.stock={}
        self.pointsSock = {}


    def run(self):
        temp_dict={}


#---------------------------------Accept players ---------------------------------------------
        while(not self.players_logged):
            #print(self.players)
            if(len(temp_dict)!=len(self.players)):
                temp_dict=self.players.copy()
                for addr in temp_dict:
                    if(temp_dict[addr][1]==0):
                        clSock=temp_dict[addr][0]
                        state=temp_dict[addr][1]
                        username=self.waitingRoom.logging(clSock) 
                        player=[clSock,state,username]
                        temp_dict.update({addr:player})
                        temp_dict[addr][1]=1
                        self.players[addr]=temp_dict[addr]

        
            if(self.waitingRoom.logged==self.players_nr):
                self.players_logged=True
        
        print("------------------------------Array de chaves públicas") # chaves esão na ordem da playerList
        print(self.waitingRoom.publicKeys)

        print("------------------------------Array de chaves de sessão") # chaves estão na ordem da playerList
        print(self.waitingRoom.symetricKeys)
        print(self.players) # jogadores por ordem de entrada

        self.game.orderList(self.players)
        self.game.printOrderList()
        
        self.sendPlayerList() #send player list
        self.sendPublickKeys()#send publick keys to everyone
        
        
#----------------------------Randomization stage-----------------------------------------------------------
       
        self.randomization_order = [p[0] for p in list(self.players.values())] #ordem de cifragem na randomização
        #randomization_order=self.game.order_list.copy()
        
        print("Randomization Order:")
        print(self.randomization_order)
        
        deckRan = self.game.domino_tableboard.domino_tilesJSON


        print(deckRan)
       
        for playerSocket in self.randomization_order:
            
            self.sendTileDeckForRandomization(playerSocket, deckRan)
            deckRan = self.msg.receive_input(playerSocket, 20480) 
          
       
        print("Randomized Deck:")
        print(eval(deckRan))
        
        self.game.domino_tableboard.domino_tilesJSON = eval(deckRan)
    
        firstPlayerSock=random.choice(list(self.players.values()))[0]

        self.sendTileDeck(firstPlayerSock) #encrypted

        recvDataDest=self.msg.receive_inputDest(firstPlayerSock) #receiving encrypted message
       
        destSock=self.getPlayerSock(recvDataDest[0])

        
        originSock = firstPlayerSock

        count_full = 0
        distribution = True

#-----------------------Selection stage-----------------------------------------------------------     

        while (1): #tiles destribution, 7 pieces to each
            
            if (recvDataDest[1] == "Full Hand"):
                print("FULL HAND")
                print(count_full)
                count_full += 1
                
                originSock.send(b'received')

                recvDataDest=self.msg.receive_inputDest(originSock, integrityKey = self.getSessionKey(originSock))

                if count_full == len(self.players):
                    break
                

            if(recvDataDest[2]):

                self.msg.send_data(destSock,"establishingKey",recvDataDest[1]) #sending message with session key between players

                print(destSock.recv(1024))
                originSock.send(b'can send the deck')
                
                recvDataDest=self.msg.receive_inputDest(originSock, integrityKey = self.getSessionKey(originSock))
           
            else:
             
                self.msg.send_data(destSock,"sendTileDeck",recvDataDest[1], crypt = True, origin = originSock.getpeername())
                print(destSock.recv(1024))
                
                recvDataDest=self.msg.receive_inputDest(destSock, integrityKey = self.getSessionKey(destSock)) #receiving encrypted message

                originSock = destSock
                destSock=self.getPlayerSock(recvDataDest[0])

        self.msg.send_data(originSock,"sendStock", "No data")
        self.stock = self.msg.receive_input(originSock, 20480, True, self.getSessionKey(originSock), integrityKey = self.getSessionKey(originSock))

        print("Stock at the end of destribuition")
        print(self.stock)

#------------------------------Bit commitment ------------------------------------------------------
        flag=False
        while(not flag):
            clientSock=self.game.order_list[self.current_in_order][1]
            clAddr=self.game.order_list[self.current_in_order][0]
            self.msg.send_data(clientSock,"commitHand","commitHand")
            firstCommit=self.msg.receive_input(clientSock, 20480, integrityKey = self.getSessionKey(clientSock))
            print("Receive first commit = " + str(firstCommit) + " from " + str(clAddr))
            #firstCommit = json.loads(firstCommit)
            R1,b=eval(firstCommit)
            self.playersCommit.update({clAddr:{"b":b,"R1":R1}})
            flag=self.controlNextPlayer()
        
        print(self.playersCommit)
        self.sendAll("getPlayersCommit",str(self.playersCommit))


#--------------------------------Revelation stage--------------------------------------------------------------
        for playerSock in self.randomization_order[::-1]:
            self.msg.send_data(playerSock, "sendReveal", self.stock, True, self.getSessionKey(playerSock), integrityKey = self.getSessionKey(playerSock)) #take the stock of
            reveal_map = self.msg.receive_input(playerSock, 40480, True, self.getSessionKey(playerSock), integrityKey = self.getSessionKey(playerSock))
            self.reveal_map_by_order.append(reveal_map)
            #send map to all players
            for player in self.players:
                next_playerSock = self.players[player][0]
                if next_playerSock != playerSock:
                    self.msg.send_data(next_playerSock, "decipheringHand", reveal_map, True, self.getSessionKey(next_playerSock), integrityKey = self.getSessionKey(next_playerSock))
                    print(self.msg.receive_input(next_playerSock, 1024))
         

        #self.msg.receive_input()
        

        
#-----------------------------de-anonymization stage-------------------------------------------------------------------
        print("anonymization stage")
        random_player = random.choice(list(self.players.values()))[0]
        self.msg.send_data(random_player,"de-anonymization",self.de_anonymizationPubKey,  integrityKey = self.getSessionKey(random_player))
        recvDataDest = self.msg.receive_inputDest(random_player,  integrityKey = self.getSessionKey(random_player))
        destSock = self.getPlayerSock(recvDataDest[0])
        originSock = random_player
        while(1):
            
            if (recvDataDest[1] == "de-anonymization complete"):
                print("de-anonymization complete")
                
                
                originSock.send(b'received')

                recvDataDest=self.msg.receive_inputDest(originSock,integrityKey = self.getSessionKey(originSock))
                self.de_anonymizationPubKey = recvDataDest[1]
                break
                

            self.msg.send_data(destSock,"de-anonymization",recvDataDest[1], crypt = True, origin = originSock.getpeername(), integrityKey = self.getSessionKey(destSock))
            
            
            recvDataDest=self.msg.receive_inputDest(destSock, integrityKey = self.getSessionKey(destSock)) #receiving encrypted message

            originSock = destSock
            destSock=self.getPlayerSock(recvDataDest[0])
        
        print("array = "+str(self.de_anonymizationPubKey))


#-----------------------------de-anonymization final stage ------------------------------------------------------------------
        print("anonymization final stage")
        pseudonyms = self.game.domino_tableboard.pseudonymTiles.keys()

        self.de_anonymizationPubKey = eval(self.de_anonymizationPubKey)
        mapTiles = {} 

        for p in pseudonyms:
            pseudo = self.game.domino_tableboard.getTileFromPseudonym(p)#0 -> index, 1->tilevalue, 2->key 
         
            index = pseudo[0]

            toCipher = {"key": pseudo[2], "tile": pseudo[1]}
            toCipherBytes = bytes(json.dumps(toCipher), encoding="utf8")
            

            if index in self.de_anonymizationPubKey.keys():
                publicKeyAn = serialization.load_pem_public_key(self.de_anonymizationPubKey[index],default_backend())
                cipheredTK = assymetric_encript(publicKeyAn, toCipherBytes)

                mapTiles[index] = cipheredTK
  
        for player in self.randomization_order:
            self.msg.send_data(player, "de-anonymization-final", mapTiles, crypt="True", key = self.getSessionKey(player), integrityKey = self.getSessionKey(player))

            print(player.recv(1024))


        
      #  self.game.gameEnded=True
#-----------------------------------Game flow-------------------------------------------------------------------
        flagPointsCheat=False
        #flag that indicates which mecanism found cheater
        #if true -> revealT
        #false->BC
        cheatedinBc_RevealT=True
        game_round=0
        while (not self.game.gameEnded):
            clientSock=self.game.order_list[self.current_in_order][1]
            clientAddr=self.game.order_list[self.current_in_order][0]
            print("Current client playing is"+str(clientAddr))  
            cheater_flag,tupleChoice, has_tile,playedTile =self.game.myTurn(clientAddr,self.players[clientAddr][2],clientSock,self.current_in_order,self.stock)
            
            # player_moves.append(tupleChoice)
            # self.game.gameRegister.update({clientAddr:{self.players[clientAddr][2]:player_moves}})
            
            if(not playedTile):
                cheater_flag,tupleChoice, has_tile=self.stockUse(clientAddr,clientSock,cheater_flag,tupleChoice,has_tile,pseudonyms)
            
            print("Client answer:"+str(tupleChoice))
            print("Cheater Flag (client):"+str(cheater_flag))
            if(cheater_flag):
                cheatedinBc_RevealT=self.playerCheatingProtest(tupleChoice,clientAddr)
                flagPointsCheat=True
                self.game.gameEnded=True
                
            else:
                #check for cheaters ( repeated tiles in board)
                flag,tile=self.checkCheaters(self.game.domino_tableboard.board)
                if(flag):
                    #print("ENTER SERVER PROTEST")

                    suspicious_players=list()
                    suspicious_players.append(clientAddr)

                    second_cheater=self.get_secondSus(tile,clientAddr)
                    #this is just to guarantee that the same player has played twice a tile 
                    if(second_cheater!=None):
                        #print("First cheater is "+ str(clientAddr))
                        #print("Second cheater is "+str(second_cheater))
                        suspicious_players.append(second_cheater)
                    #ask for second commit 
                    self.ask_secondCommit(suspicious_players)

                    flagPointsCheat=True
                    #Check BC to find Cheater
                    cheater,cheatedinBc_RevealT=self.findCheaterWithBC(suspicious_players,tile)
                    #if BC don't find Cheater than server must Reveal T
                    if(cheatedinBc_RevealT):
                        self.findCheaterRevealinT(suspicious_players,tile)

                    self.game.gameEnded=True
                
            self.controlNextPlayer()
        
        #if(flagPointsCheat)

        #if someone cheated 
        #server must check if all players agree 
        if(flagPointsCheat):
            playersCheatersList=list()
            
            if(cheatedinBc_RevealT):
                playersCheatersList=self.sendAll("SendCheatersList","RevealedT",flagPointsCheat).copy()
            else:
                playersCheatersList=self.sendAll("SendCheatersList","BC",flagPointsCheat).copy()
            
            agreement=self.checkAgreementCheater(playersCheatersList)
            if(agreement):
                self.sendAll("AgreementAchieved","All players agreed in cheater, game is Over!")
        
        else:
            if(flagPointsCheat!=None and not flagPointsCheat):
                self.calculatePlayerPoints(flagPointsCheat)
                self.declareWinner(flagPointsCheat)
            self.sendAll("Quit",None,flagPointsCheat)
            print("Final size of Stock")
            print(len(self.stock))
            print("GAME ENDED!!!")
            
        threading.Thread._delete(self)
        
        

#-----------------------------------------------end-----------------------------------------------------------


    def controlNextPlayer(self):
        last_flag=False #flag just to check if it's the last or not 

        self.game.printOrderList()
        if(not self.game.checkPlayerFlag(self.current_in_order)): #Player is not /choosing
            if(self.current_in_order==self.players_nr -1 ):#end of cycle
                self.current_in_order=0
                last_flag=True

            else:
                self.current_in_order+=1
                last_flag=False
        
        return last_flag

    #tell the players that the game is Over!!
    def sendAll(self,msg,data=None,flagCheat=None):

        playersCheatersList=list()
        for addr in self.players:
            clSock= self.players[addr][0]
            if (data==None):#Quit!
                self.msg.send_data(clSock,msg,msg)
                self.msg.receive_input(clSock,5120)
            else:
                #print(data)
                self.msg.send_data(clSock,msg,data)
                ans=self.msg.receive_input(clSock,5120)
                if(flagCheat!=None and flagCheat):
                    playersCheatersList.append(ans)
           # self.controlNextPlayer()
        return playersCheatersList
       
    #send the points for the players
    def calculatePlayerPoints(self,flagCheat):
        for i in range(0,self.players_nr):
            clSock=self.game.order_list[self.current_in_order][1]
            if(not flagCheat):
                self.msg.send_data(clSock,"GetPlayerPoints","points")

                msgcc = clSock.recv(8192)

                if(self.cc_disabler==0):
                    if(verifySign(getCerts(),self.waitingRoom.usernames_sock[clSock],msgcc)):
                        print("Success!")

                player_hand = self.msg.receive_input(clSock, 20480, True, self.getSessionKey(clSock),integrityKey = self.getSessionKey(clSock))
                points=0
                for data in player_hand:
                    tile=(domino(data['data']['bottom'],data['data']['top']))
                    tilepoints = tile.getBottom()+tile.getTop()
                    points+=tilepoints
                
                self.pointsSock.update({self.waitingRoom.usernames_sock[clSock]:points})

                self.msg.send_data(clSock, "points",str(points), True, self.getSessionKey(clSock),integrityKey = self.getSessionKey(clSock))
                print(self.msg.receive_input(clSock,1024))
            self.controlNextPlayer()

    #declare the winner and send that to the players
    def declareWinner(self,flagCheat):

        for i in range(0,self.players_nr):
            clSock=self.game.order_list[self.current_in_order][1]
            if(not flagCheat):
                winnerdict=min(self.pointsSock.items(), key=lambda x: x[1]) 

                winnerstr= "The winner is "+winnerdict[0]+" with " + str(winnerdict[1]) + " points!!"
                print(winnerstr)

                self.msg.send_data(clSock, "GetWinner",json.dumps(winnerstr), True, self.getSessionKey(clSock),integrityKey = self.getSessionKey(clSock))
                
                print(clSock.recv(1024))

            self.controlNextPlayer()

        
    
    #send the list of players for each player 
    def sendPlayerList(self):
        
        for player in self.players:
            clSock=self.players[player][0] #clientSocket
            self.msg.send_data(clSock,"sendPlayersList",self.getPlayerAddrList(), True, self.getSessionKey(clSock))

    #Send map of public keys to players
    def sendPublickKeys(self):
        for player in self.players:
            clSock=self.players[player][0] #clientSocket
            addr_list = self.waitingRoom.publicKeys.keys()
            
            for addr in addr_list:
                
                pubKey = self.waitingRoom.publicKeys[addr]
                self.msg.send_data(clSock, "sendingPublicKeys", addr)
                print(clSock.recv(8192))
                clSock.send(pubKey.public_bytes(serialization . Encoding . PEM, serialization.PublicFormat. PKCS1))
                print(clSock.recv(8192))

                
    #returns a list with players addr
    def getPlayerAddrList(self):
        playerAddrList=list()
        for player in self.players:
            playerAddrList.append(player)
       
        return  playerAddrList

    def getSessionKey(self, clSock):
        p = self.getPlayerAddrList()
        index = p.index(clSock.getpeername())
        
        return self.waitingRoom.symetricKeys[index]
    #send tile deck to the respective clSock 
    def sendTileDeck(self,clSock):
        clientSymkey = self.getSessionKey(clSock)

        
        self.msg.send_data(clSock,"sendTileDeck",self.game.domino_tableboard.domino_tilesJSON, True, clientSymkey) #sendDominoTiles to player encrypted
        self.msg.receive_input(clSock,1024)

    def sendTileDeckForRandomization(self,clSock, toRandomize): #send and receive
        clientSymkey = self.getSessionKey(clSock)
        self.msg.send_data(clSock, "tilesRandomized", toRandomize,True, clientSymkey)

        self.msg.receive_input(clSock,1024) # 200-ok

    def receiveTiles(self, clSock, size):
        receivedList = list()
        for x in range(size):
            receivedList.append(self.msg.receive_input(clSock,10240))
            clSock.send("receivedTile".encode())

        return receivedList

    # returns socket giving the adress
    def getPlayerSock(self,clAddr):
        
        #print("PLAYERS="+str(self.players))
        for addr in self.players:
            #print("Addr="+str(addr[1])+"=="+ str(clAddr[1]) +"ClAddr")
           # if(addr!=None)
            if(addr[1]==clAddr[1]):
                #print(self.players[addr][0])
                return self.players.get(addr)[0]


#------------------Stock use -------------------------------------------

    def stockUse(self,clientAddr,clientSock,flag,choice,tileFlag,pseudonyms):
        cheater_flag=flag
        tupleChoice=choice
        #print("tuplechoice")
        #print(tupleChoice)
        has_tile=flag
        #print("has_tile:")
        #print(has_tile)
        while not has_tile:
                cheater_flag,tupleChoice, has_tile,playedTile =self.game.myTurn(clientAddr,self.players[clientAddr][2],clientSock,self.current_in_order,self.stock)

                if not has_tile:
                    self.msg.send_data(clientSock,"pickingStock", self.stock, integrityKey = self.getSessionKey(clientSock))
                    stock_tile = self.msg.receive_input(clientSock, 4094, decode = True, integrityKey = self.getSessionKey(clientSock))
                    #print("stoocckk")
                    #print(stock_tile)
                    keys_to_send = []

                    self.stock.remove(stock_tile)

                    for p in self.randomization_order[::-1]:
                        self.msg.send_data(p, "sendKeyForPiece", stock_tile, integrityKey = self.getSessionKey(p))
                        key, iv = self.msg.receive_input(p, 4094, decode = True, integrityKey = self.getSessionKey(p))
                        print("keyyy", key)

                        dict_key = {"key": str(key), "iv": str(iv)}
                        dict_key_bytes = bytes(json.dumps(dict_key), encoding="utf8")

                        keys_to_send.append(dict_key_bytes)

                        #print("to_Sendddd")
                        print(keys_to_send)

                        stock_tile = decrypt([stock_tile,iv], key)


                    self.msg.send_data(clientSock, "pieceFromStock", keys_to_send, integrityKey = self.getSessionKey(clientSock))

                    tilePseudo = self.msg.receive_input(clientSock, 2048, decode = True, integrityKey = self.getSessionKey(clientSock))
                    
                    tilePseudo = eval(tilePseudo.decode())

                    if tilePseudo["data"] in pseudonyms:
                        print(tilePseudo["data"])
                        
                        pseudo = self.game.domino_tableboard.getTileFromPseudonym(tilePseudo["data"])#0 -> index, 1->tilevalue, 2->key 

                        index = pseudo[0]

                        toCipher = {"key": pseudo[2], "tile": pseudo[1], "index": index}
                        toCipherBytes = bytes(json.dumps(toCipher), encoding="utf8")
                        
                        print(toCipherBytes)

                        self.msg.send_data(clientSock, "yourPiece", toCipherBytes, integrityKey = self.getSessionKey(clientSock))
                        print(self.msg.receive_input(clientSock,5120))
        
        return cheater_flag,tupleChoice, has_tile

    #player protest
    def playerCheatingProtest(self,tupleChoice,clientAddr):
        
        #print("ENTER CHEATING PROTEST")
        suspicious_players=list()
        suspicious_players.append(clientAddr)
        bc_flag=False
        #print("TUPLECHOICE:"+str(tupleChoice))
        #for tile_played in tupleChoice:
        tile_played=tupleChoice
        print(tile_played)
        tile=domino(tile_played["data"]["bottom"],tile_played["data"]["top"])
        #print(tile)
        second_cheater=self.get_secondSus(tile,clientAddr)
        if(second_cheater!=None):
            #print("First cheater is "+ str(clientAddr))
            #print("Second cheater is "+str(second_cheater))
            suspicious_players.append(second_cheater)

        self.ask_secondCommit(suspicious_players)

        cheater,bc_flag=self.findCheaterWithBC(suspicious_players,tile)
        #if BC don't find Cheater than server must Reveal T
        print("Bc_flag="+ str(bc_flag))
        if(bc_flag):
            self.findCheaterRevealinT(suspicious_players,tile)

        return bc_flag
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

                #print("Rep tile:"+ str(domino_reptile) + "== " +str(domino_tile) + " :Tile")
                if(domino_tile.equalTile(domino_reptile)):
                    print("CHEATER CAUGHT!!")
                    cheater_flag=True
                    cheater_tile=domino_tile
                    return cheater_flag,cheater_tile
    
        return cheater_flag ,cheater_tile
    
    #cheater was caught!
    #check who played repeated tiles
    def get_secondSus(self,tile,firstCheater):
        
        print("Repeated tile is " + str(tile))
        #print(firstCheater)
        secondSus=None
        for move in self.game.gameRegister:
            #converts to domino just to facilitate the comparison
            for addr,username in move:
                print("Client Addr is" + str(addr))
                data=move[(addr,username)]
                tileJson,side,inverted=data[0],data[1],data[2]
                if addr!=firstCheater:
                    print("PLAYS="+str(data))
                    #print(player_moves)
                    if(tileJson["index"]!=-1): #discard invalid moves
                        domino_tile=domino(tileJson["data"]["bottom"],tileJson["data"]["top"])
                        if(domino_tile.equalTile(tile)):
                            #position=player_moves.index(d)
                            #clientAddr=playersAddr[position]
                            print("Second Cheater is ="+str(addr))
                            secondSus=addr
        return secondSus       

    def ask_secondCommit(self,listCheaters):
        
        print("Susp list is")
        print(listCheaters)
        #if(len(listCheaters))

        for addr in listCheaters:
            clientSock=self.getPlayerSock(addr)
            self.msg.send_data(clientSock,"secondCommit","secondCommit")
            secondCommit=self.msg.receive_input(clientSock, 20480, integrityKey = self.getSessionKey(clientSock))
           # print(secondCommit)
            #secondCommit=json.loads(secondCommit)
            R2,Tiles = eval(secondCommit)
           # print("TILES=="+ str(Tiles))
            R1,b=self.playersCommit.get(addr)["R1"],self.playersCommit.get(addr)["b"]
            #self.playersCommit.
            self.playersCommit.update({addr:{"b":b,"R1":R1,"R2":R2,"T":Tiles}})

        self.sendAll("CheaterCaught","Illegal move caught!Checking for cheaters")
        self.sendAll("getPlayersCommit",str(self.playersCommit))
        print(self.playersCommit)

    
    def hand_reveal(self, t):
        
        deciphered_hand = list()
        hand = t.copy()

        for count in range(0,self.players_nr):
            
            if(count >= 1 ):
                hand = deciphered_hand.copy()
                deciphered_hand = list()
            for tile in hand:
                tmp_map = self.reveal_map_by_order[count].copy()
                key, iv = tmp_map[tile]
                deciphered_tile = decrypt([tile, iv], key)
                deciphered_hand.append(deciphered_tile)


          
        return deciphered_hand

    
    #finding cheater in two ways:
    #1-> after asking for second commit check if BC checks with the first commit  
    #2-> if "1" doesn't find who is the cheater server must reveal pseudonyms 

    #trys to find cheater only using BC 
    def findCheaterWithBC(self,listCheaters,forgedTile):
        
        flag_commit=False 
        cheater=""
        reptileFounded=False
        #it can be 2 cheaters (if they play the same tile that are not from them)
        cheater=[]
        #if same player has played the same tile twice
        if(len(listCheaters)==1):
            #print("only one cheater!")
            cheater = listCheaters
            #return cheater,flag_commit
        else:
            checkBC=False
            for addr in self.playersCommit:
                if addr in listCheaters:
                    commit=self.playersCommit[addr]
                    #print(commit)
                    b,R1,R2,T=commit["b"],commit["R1"],commit["R2"],commit["T"]
                    checkBC=check_commit(T,R1,R2,b) #check if BC is generated correctly
                    #if false Cheater founded !!
                    #print("FLAG=="+str(checkBC))
                    if(not checkBC):
                        cheater.append(addr)

        #if cheater founded!
        if len(cheater)>0:                
            cheater_count=0
            if(len(cheater)>1):
                for c in cheater:
                 #   print("ENVIAR O CHEATER!" + str(cheater_count))

                    self.sendAll("Cheater","["+str(cheater_count)+"]Cheater is " + str(self.players[c][2]) + " with addr "+ str(c))
                    cheater_count+=1

            else:
               # print("ENVIAR O CHEATER!")
                self.sendAll("Cheater","Game ended :Cheater is " + str(self.players[cheater[0]][2]) + " with addr "+ str(cheater[0]))
            
        else:
            flag_commit=True

        return cheater,flag_commit

    
    #try to find cheater revealing T 
    def findCheaterRevealinT(self,listCheaters,forgedTile):
        
        flag_commit=False 
        cheater=""
        reptileFounded=False
        #it can be 2 cheaters (if they play the same tile that are not from them)
        cheater=[]
        #if same player has played the same tile twice
        if(len(listCheaters)==1):
            cheater = listCheaters
            #return cheater,flag_commit
        else:
            for addr in self.playersCommit:
                #print("player hand Commit stage ")
                #print(pseudonymTiles)
                commit=self.playersCommit[addr]

                if addr in listCheaters and "R2" in commit.keys() and "T" in commit.keys():
                    b,R1,R2,T=commit["b"],commit["R1"],commit["R2"],commit["T"]
                    print(commit)
                    pseudonymTiles= self.hand_reveal(list(T).copy())

                    index=0
                    curretAddTileFound=False
                    for tile in pseudonymTiles:
                        jsonTile={}
                        jsonTilePseudonym=eval(tile.decode("utf-8"))
                        tileInfo=self.game.domino_tableboard.getTileFromPseudonym(jsonTilePseudonym["data"])
                        jsonTile["index"]=tileInfo[0]
                        jsonTile["data"]=tileInfo[1]
                        #converts to tile just to check if tile is equal 
                        #it's more pratic to compare
                        dominoTile=domino(jsonTile["data"]["bottom"],jsonTile["data"]["top"])
                        #print("DominoTile="+str(dominoTile))
                        #print("Forged="+ str(forgedTile))
                        self.sendAll("RevealingHands",str((index,addr,forgedTile.data,jsonTile)))
                        #self.sendAll("RevealingHands",str(addr) + " forgedTile:"+ str(forgedTile)+" Reveal tile Hand["+str(index)+"]:" + str(dominoTile))
                        index+=1
                        if(forgedTile.equalTile(dominoTile)):
                            reptileFounded=True
                            curretAddTileFound=True

                    if((not reptileFounded and not curretAddTileFound ) or (reptileFounded and not curretAddTileFound )):
                        cheater.append(addr)
                        


        cheater_count=0
        if(len(cheater)>1):
            for c in cheater:
                self.sendAll("Cheater","["+str(cheater_count)+"]Cheater is " + str(self.players[c][2]) + " with addr "+ str(c))
                cheater_count+=1
        else:
            self.sendAll("Cheater","Cheater is " + str(self.players[cheater[0]][2]) + " with addr "+ str(cheater[0]))

        return cheater,flag_commit


    #checks if all players agree on the cheater(s)
    def checkAgreementCheater(self,listCheaters):
        
        agreement=False
        #check if all elements are equal
        agreement=all(elem==listCheaters[0] for elem in listCheaters)
        #print("RESULT="+str(result))
        return agreement
            

if __name__ == "__main__":
   main()

