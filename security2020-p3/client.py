import socket
import sys
import time 
import json
import pickle
import random
import os
import hashlib
import ast
import base64
import threading
from math import *
from domino import *
from send_receive import *
from symetric_functions import *
from cryptoAssym import *
from cartaocidadao import *
from random_username.generate import generate_username
from bit_commitment import *




def main():

    try:
        print(sys.argv[1])
    except:
        print("Please enter:\n[arg1]->->cheater maxim probability: 0-100")
        exit(1)

    maximProbCheater=int(sys.argv[1])
    if(maximProbCheater<0 or maximProbCheater>100):
        print("Probability '" +str(maximProbCheater)+"' is invalid please try again [arg2]:cheater Maxim probability ( 0-100)\n")
    else:
        playAgain=""
        username=""
        while(playAgain!="n"):
      
            p=Player(maximProbCheater,username)
            username=p.start()
            playAgain=""
            while(playAgain!="n" and playAgain!="y" ):
                playAgain=input("Do you want to play again?(y/n):")




class Player ():
   
    def __init__(self,maximProbCheater,username):
        self.maximProbCheater=maximProbCheater
        self.username=username

    def start(self):
        playerTh=playerThread(self.maximProbCheater,self.username)
        playerTh.start()
        playerTh.join()
        self.username=playerTh.username
        print("Goodbye "+ self.username+" !")

        return self.username


class playerThread(threading.Thread):

    def __init__(self,maximProbCheater,username):
        threading.Thread.__init__(self)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 8000
        self.addr = (self.host, self.port)
        self.server_msg=""
        self.player_hand=list()
        self.action=""
        self.data=""
        self.board=list()
        self.connect()
        self.msgtoClient=msgCommunication()
        self.playersList={}
        self.tilePlayed = None
        self.botCount=0

        self.points=0
        
        #keys generation
        self.private_key = assymetric_key_generator()
        self.public_key = self.private_key.public_key()
        self.players_session_keys = {}
        self.players_public_keys = {}
        self.player_addr = ()

        self.server_public_key = 0
        self.session_key = 0
        
        self.players_commit={} #{addres: 1stCommit , 2nd Commit}
        self.cipher_map = {} #map C->K
        self.deck_to_cipher = list()

        self.hand_full = False
        self.tiledeck = []

        self.de_anonymizationPrivKey = {}

        self.deck_to_cheat=self.readTilesinFile()

        #cheater probability 
        self.maximProbCheater=maximProbCheater
        #forged tile 
        self.cheater_move=[]
        #list that contains cheaters list for current player
        self.cheatersList=list()
        #list that contains players that not cheated 
        #list used when server revealed T just to compare with the previous one
        self.cleanList=list()
        #flag that informs if a player cheated or not 
        self.cheaterFlag=False
        #flag that informs if current player cheated 
        self.currentPl_cheated=False

        #Citizen Card
        self.cc_disabler = 1
        self.username=username
        self.gameRegister={}

 
    #player flow/actions
    def run(self):

        while(self.action!="Quit"):
            self.updateServerMsg() #this update is only to get the Action 

            if self.action=="Print":
                self.printServer()
            elif self.action=="PrintQuit":
                self.printServer()
                break
            elif(self.action=="Auth"):
                self.authentication()
                    
            elif(self.action=="pubKey"): #cliente envia a chave publica para o server
                self.getPublicKey()

            elif(self.action=="sign"):
                self.sendSignature()
            
            elif(self.action == "serverKey"):
                self.sendServerKey()
            
            elif(self.action == "symKey"):
                self.giveMeSymetricKey()

            elif(self.action == "sendingPublicKeys"): #cliente recebe as chaves de todos os clientes
                self.sendPublicKeys()

            elif(self.action=="sendPlayersList"):
                self.playersList=self.data 

            elif(self.action == "tilesRandomized"): #receiving tiles randomized, one by one, deck to large to send all at once
                self.randomizationStage()
                   
            elif(self.action == "establishingKey"):
                self.establishKey()
            
            elif(self.action=="sendTileDeck"):
                deckTiles = self.sendTileDeck()

            elif(self.action == "sendStock"):
                self.sendStock(deckTiles)
                
            elif(self.action=="sendReveal"):
                self.sendReveal()
                
            elif(self.action=="decipheringHand"):
                reveal_map = self.data
                
                self.revealHand(reveal_map)
               
                self.s.send(b'received map')

            elif(self.action == "de-anonymization"):
                self.deAnonymization()

            elif(self.action == "de-anonymization-final"):
                self.deAnonymizationFinal()
                    
            elif(self.action=="commitHand"):
                #generates commit
                self.commit_generation()
                #publish first part of commit
                self.publish_Commit(1)
            
            elif(self.action=="getPlayersCommit"):
                #receive commit from players
                self.players_commit=eval(self.data)
                self.send_data("Received players commit!")
                print("Received players commit")
                #checkForCheater
                if(self.cheaterFlag):

                    self.cheatersList=self.checkBitCommitment().copy()
                    #print(self.cheatersList)
            
            elif(self.action=="GameRegister"):
                print("--------------------------------------------------Game Moves:----------------------------------------------------------------")

                self.gameRegister.clear()
                self.gameRegister=eval(self.data).copy()
                self.printMoves()
                self.send_data("Players moves received!")
                print("------------------------------------------------------------------------------------------------------------------------------")


            elif(self.action=="secondCommit"):
                print("Sending my secondCommit")
                self.publish_Commit(2)

                #self.send_data("200-Ok")
            elif(self.action=="RevealingHands"):
                #print(self.data)
                index,addr,forgedTileJson,dominoTileJson=eval(self.data)
                forgedTile=domino(forgedTileJson["bottom"],forgedTileJson["top"])
                dominoTile=self.jsonToDomino(dominoTileJson)
                
                print(str(addr)+": playedTile[" + str(index) + "]=" + str(dominoTile)+ " forgedTile= "+str(forgedTile))
                self.findSuspRevealed(addr,forgedTile,dominoTile)
                self.send_data("200-OK")
                #self.printServer() 

            elif(self.action=="SendTile"):
                self.printTiles(self.player_hand,"Player hand")
                print("------------------------------------------------------------------------------------------------------------------------------")

                flag,self.cheater_moves=self.checkForCheaters()
                if(flag):
                    self.send_data("Cheater caught!")
                else:    
                    self.sendTile()

            elif(self.action=="CheaterCaught"):
                self.cheaterFlag=True
                self.printServer()
                
            
            elif(self.action=="pickingStock"):
                stock = self.data
                tileStock = self.pickStockTile(stock)
                print("Pick a Stock tile: ")
                print(tileStock)
                self.msgtoClient.send_data(self.s, "choosedTile", tileStock,  integrityKey = self.session_key)

            elif(self.action == "sendKeyForPiece"):
                piece = self.data 
                key = self.cipher_map[piece]
                self.msgtoClient.send_data(self.s, "key", [key[0], key[1]],  integrityKey = self.session_key)

            elif(self.action == "pieceFromStock"):
                array_keys = self.data

                tile = tileStock
                for k in array_keys:
                    key_decoded = k.decode()

                    key_decoded = json.loads(key_decoded)
                 
                    key = eval(key_decoded["key"])
                    
                    iv = eval(key_decoded["iv"])

                    tile = decrypt([tile, iv], key)

                self.msgtoClient.send_data(self.s, "de_anon_stock", tile,  integrityKey = self.session_key)
                #tile_value = self.msgtoClient.receive_input(self.s, 2048)
            
            elif(self.action == "yourPiece"):
                tile = self.data

                tile = json.loads(tile.decode("utf8"))
                
                print("Tile picked from stock: ")
                x = {"index": tile["index"], "data": tile["tile"]}
                print(self.jsonToDomino(x))
                
                self.player_hand.append(x)
                self.send_data("200-Ok")

            elif(self.action=="Send suspicious moves"):
                self.s.send(bytes(json.dumps(self.cheater_moves),encoding="utf8"))

            elif(self.action=="Cheater"):
                self.printServer()

            elif(self.action=="SendCheatersList"):
                
                if(self.data=="RevealedT"):
                    suspicious_players=self.cheatersList.copy()
                    self.cheatersList.clear()
                    for suspAddr in suspicious_players:
                        if(suspAddr not in self.cleanList):
                            self.cheatersList.append(suspAddr)
                                   
                print("CheatersList="+str(self.cheatersList))
                self.s.send(bytes(json.dumps(self.cheatersList),encoding="utf8"))
                #self.send_data("200-Ok")
            elif(self.action=="AgreementAchieved"):
                self.printServer()
                self.action="Quit"


            elif(self.action=="PrintBoard"):
                print("-----------------------------------------------------Board---------------------------------------------------------------------")
                self.board=self.data
                self.printTiles(self.board,"board")
                print("-------------------------------------------------------------------------------------------------------------------------------")

                print("\n---------------------------------------------------PlayerHand----------------------------------------------------------------")
                self.send_data("200-Ok")

            elif(self.action=="RemoveTile"):
                self.removeHandTile()
            
            elif(self.action=="CheckifEmpty"):
                self.checkifHandisEmpty()

            elif(self.action=="GetPlayerPoints"):
                self.getPlayerPoints()

            elif(self.action=="GetWinner"):
                winner = self.data
                self.send_data("200-Ok")
                print(winner)
        
        #print("Game is done!")
        #self.send_data("I am going to quit")
        return 
        #threading.Thread._delete(self)

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
                                              
    #print data from server 
    def printServer(self):
        print("[TableManager]"+str(self.data))
        self.send_data("200-Ok")

    def authentication(self):
        if(self.data=="Logged Sucessufully"):
            print("Waiting in Lobby...")
            self.send_data("200-Ok")
        else:   
            if(self.data=="\nUsername:"):
                if(self.username==""):
                    message=generate_username()
                    self.username = message[0]
                
                print("Username is "+self.username)
                self.send_data(self.username)

    def getPublicKey(self):
        if(self.data=="Give me your public key"):
            self.s.send(self.public_key.public_bytes(serialization . Encoding . PEM, serialization.PublicFormat. PKCS1))
            print("Public key sent!")
    
    def sendSignature(self):
        if(self.data=="Send Signature"):
            self.s.send(signing(self.private_key))
            print("Signature sent!")

    def sendServerKey(self):
        if(self.data=="Sending my key"):
            self.send_data("200-OK")
            self.server_public_key = serialization.load_pem_public_key(self.s.recv(8192), default_backend()) #Get the Server Key from Server
            self.send_data("200-OK")
            print("Got Server public key!")

    def giveMeSymetricKey(self):
        if(self.data=="Give me symmetric key"):
            self.session_key = secretkey(word_generator())
            keyEncrypted = assymetric_encript(self.server_public_key, self.session_key)
            self.s.send(keyEncrypted)
            print("Session key sent!")      
            
    def sendPublicKeys(self):            

        address = (self.data[0],self.data[1])
        
        self.send_data("200-Ok")
        playerKey = serialization.load_pem_public_key(self.s.recv(8192), default_backend())
        self.players_public_keys[address] = playerKey
        self.send_data("200-Ok")

    def establishKey(self):
        print("to decipher")
        print(self.data)
        deciphered_str = assymetric_decrypt(self.private_key,eval(self.data))
        deciphered = eval(deciphered_str) # reverse of str(msg).encode()
        
        self.send_data("Key established")
        self.player_addr = deciphered[0]
        session_key = deciphered[1]
        self.players_session_keys[self.player_addr] = session_key


    def randomizationStage(self):   
        self.deck_to_cipher = self.data
        self.send_data("200-Ok")
        deck_ciphered = self.randomization(self.deck_to_cipher)
        random.shuffle(deck_ciphered)
        self.send_data(str(deck_ciphered))

    def randomization(self, deck):
        ciphered_deck = list()
        
        if not isinstance(deck, list):
            deck = eval(deck)
        
        for tile in deck:
    
            key = secretkey(word_generator())

            if(isinstance(tile, dict)):
                result = encrypt(str(tile).encode(), key)
            
            else:
                result = encrypt(tile, key)

            while result[0] in ciphered_deck: #deteção de colisoes e calculo de nova chave
                print("cipher collision")
                key = secretkey(word_generator())

                if(isinstance(tile, dict)):
                    result = encrypt(str(tile).encode(), key)
            
                else:
                    result = encrypt(tile, key)

            
            self.cipher_map[result[0]] = (key, result[1]) #storing key + iv for each tile

            
            
            ciphered_deck.append(result[0])

        
        return ciphered_deck

    def sendTileDeck(self):
        deckTiles=self.recieveTiles() 
        self.send_data("200-Ok")

        if not self.hand_full and  len(self.player_hand) == 7: # end game for 28 tiles
            print("My Hand is Full")

            self.msgtoClient.send_data_dest(self.s,self.player_addr,"Full Hand", integrityKey  = self.session_key) #sending to server the rest of the deck
            print(self.s.recv(1024))
            self.msgtoClient.send_data_dest(self.s,self.player_addr,deckTiles,True, self.players_session_keys[self.player_addr], integrityKey  = self.session_key)
            #self.msgtoClient.send_data(self.s, "stock",deckTiles, True, self.session_key)

            self.hand_full = True
            
        else:
            tiledeck=self.choosingTile(deckTiles)
        
            print("My Hand ciphered:")
            print(self.player_hand)
            self.player_addr = self.randomNextPlayer()
            
            if(self.check_session_key(self.player_addr)):
                self.msgtoClient.send_data_dest(self.s,self.player_addr,tiledeck,True, self.players_session_keys[self.player_addr], integrityKey  = self.session_key) #sending to server
            
            else:
                msg = self.establish_key()

                destkey = self.players_public_keys[self.player_addr]
                encrypt_msg = assymetric_encript(destkey,str(msg).encode())
                self.msgtoClient.send_data_dest(self.s,self.player_addr,encrypt_msg,firstTime = True, integrityKey =self.session_key) #sending to server
                print(self.s.recv(1024))
                self.msgtoClient.send_data_dest(self.s,self.player_addr,tiledeck,True, msg[1], integrityKey =self.session_key)

        return deckTiles

    def sendStock(self,deckTiles):
        self.msgtoClient.send_data(self.s, "stock",deckTiles, True, self.session_key, integrityKey =self.session_key)
                

    def sendReveal(self):
        reveal_map = {}
        for key in self.cipher_map.keys():
            if key not in self.data: #if not in deck
                reveal_map[key] = self.cipher_map[key]

        self.msgtoClient.send_data(self.s, "maps", reveal_map, True, self.session_key, integrityKey =self.session_key)
        
        self.revealHand(reveal_map)
    

    def revealHand(self, reveal_map):
        deciphered_hand = list()

        for tile in self.player_hand:
            key, iv = reveal_map[tile]
            deciphered_tile = decrypt([tile, iv], key)
            deciphered_hand.append(deciphered_tile)

        self.player_hand = deciphered_hand

    def deAnonymization(self):
        prob=random.randint(0,100)
        if(prob<=5):
            mapa = self.data
            
            for tile in self.player_hand:
                tile = eval(tile)
                if(mapa.get(tile["index"]) == None):
                    private_key = assymetric_key_generator()
                    public_key = private_key.public_key()
                    mapa.update({tile["index"] : public_key.public_bytes(serialization . Encoding . PEM, serialization.PublicFormat. PKCS1)})
                    self.de_anonymizationPrivKey.update({tile["index"] : private_key.private_bytes(serialization . Encoding . PEM, serialization.PrivateFormat.TraditionalOpenSSL,serialization.NoEncryption())})
                    break
            
            player_dest = self.randomNextPlayer()
            #print("comprimento do  mapa === " + str(len(mapa)))
            if(len(mapa) == len(self.playersList)* 7 ):
                # print("private map")
                # print(self.de_anonymizationPrivKey)
                self.msgtoClient.send_data_dest(self.s,player_dest,"de-anonymization complete", integrityKey = self.session_key)
                print(self.s.recv(1024))
                self.msgtoClient.send_data_dest(self.s,player_dest,mapa, integrityKey = self.session_key)
            
            else:
                while player_dest not in self.players_session_keys:
                    player_dest = self.randomNextPlayer()
                self.msgtoClient.send_data_dest(self.s,player_dest,mapa,True,self.players_session_keys[player_dest], integrityKey = self.session_key)
        
        else:
            player_dest = self.randomNextPlayer()
            while player_dest not in self.players_session_keys:
                player_dest = self.randomNextPlayer()
            self.msgtoClient.send_data_dest(self.s,player_dest,self.data,True,self.players_session_keys[player_dest], integrityKey = self.session_key)

    def deAnonymizationFinal(self):
        hand_tiles = []
        for tile in self.player_hand:
            tile = eval(tile)

            idx = tile["index"]

            tilePseudo = tile["data"]

            tile = self.data[idx]
            
            privKeyAn = serialization.load_pem_private_key(self.de_anonymizationPrivKey[idx],None, default_backend())
            
            tile = assymetric_decrypt(privKeyAn,tile) 
            
            tile = json.loads(tile.decode("utf8"))
            
            x = {"index": idx, "data": tile["tile"]}

            self.verifyPseudonym(tilePseudo, idx, tile["key"], tile["tile"])#verify if table maneger didnt cheat
                
            hand_tiles.append(x) 


            #verificar com a key, se o server n enganou o jogador

        self.player_hand = hand_tiles
        self.send_data("Got it")

    def verifyPseudonym(self, pseudonym, index, key, tile):
        h2=hashlib.sha1()
        h2.update(bytes(json.dumps((index,key,tile)),encoding="utf8"))
        pseuDonym=h2.hexdigest()

        if pseudonym == pseuDonym:
            return True
        else:
            print("server cheated in giving me the tile, goodbye!")
            sys.exit()

    def check_session_key(self,claddr):
        key_lst = self.players_session_keys.keys()
        if(claddr in key_lst):
            return True
        else:
            return False

    def establish_key(self):
        symkey = secretkey(word_generator())
        self.players_session_keys[self.player_addr] = symkey
        addr = self.s.getsockname()

        cmb = (addr,symkey)
        
        return cmb

    def pickStockTile(self, stock):
        stockSize = len(stock)
        choosedTile = ""

        if stock != []:
            idx = random.randint(0,stockSize - 1)
            choosedTile = stock[idx]

        return choosedTile
        

    def choosingTile(self,deckTiles): 

        tmpdeckTiles=deckTiles.copy()
        # player must have less than 7 tiles and boarTiles shouldn't be empty
        if len(self.player_hand) < 7 and deckTiles != []:
            prob=random.randint(0,100)
            if(prob<=5):
                print("ChooseTile(y/n)?",end='')
                chooseTile="y"
            else:
                chooseTile="n"
            
            print("Prob= " + str(prob) + " answer="+chooseTile)


            
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
                            tileidx=random.randint(0,len(self.player_hand)-1)
                            print("Index choosed:"+str(tileidx))
                            tmpTile=self.player_hand[int(tileidx)]
                            
                            boardtileidx=random.randint(0,len(tmpdeckTiles)-1)
                            print("Board index choosed:"+str(boardtileidx))
                            boardTile=tmpdeckTiles[int(boardtileidx)]
                            print("Board tile choosed is "+str(boardTile))
                            tmpdeckTiles[int(boardtileidx)]=tmpTile
                            self.player_hand[int(tileidx)]=boardTile


        print("Deck tiles to send:")
        random.shuffle(tmpdeckTiles)
        #self.printTiles(tmpdeckTiles,"pseudonym")    
        print("\n")                
        return tmpdeckTiles

    #updates server message depeding 
    # action and data are updated 

    def updateServerMsg(self):

        recv = self.s.recv(40480) #bytes{  crypt: True , message : str-> cifra( str -> (message: action=blabla  data = deck)),iv].encode } 
    
        self.server_msg=json.loads(recv.decode("utf8"))

        if self.server_msg["hash"] != "": #integrity control
            mac = base64.b64decode(self.server_msg["hash"])
            integrity_check = verify_message(self.server_msg["data"], self.session_key, mac)
            if not integrity_check:
                sys.exit()

        if self.server_msg["origin"] != "None":
            
            origin_addr = self.server_msg["origin"]
            session_key = self.players_session_keys[(origin_addr[0], origin_addr[1])]

        else:
            session_key = self.session_key #if not, communicating with server

        if self.server_msg["crypt"]:
          
            encryptedInfo = [base64.b64decode(d) for d in self.server_msg["data"]]
            decryptedInfo = decrypt(encryptedInfo, session_key)

            self.data = eval(decryptedInfo.decode('utf-8'))

        else: self.data=self.server_msg["data"]

        if self.server_msg["decode"]:
            if isinstance(self.server_msg["data"], list):
                self.data = [base64.b64decode(d) for d in self.server_msg["data"]]

            else:
                self.data = base64.b64decode(self.server_msg["data"])

        self.action=self.server_msg["action"]

        
       
    # receive tile deck to choose a tile 
    def recieveTiles(self):
        deckTiles=list()
        try:
            if not isinstance(self.data, list): 
                deckTiles=eval(self.data).copy()
            else:
                deckTiles=self.data.copy()
        except:
            print("Failed to load")
        return deckTiles

    #send a tile to play 
    def sendTile(self):
        #print(self.data,end='')
        null={}
        null['index']=-1
        null['data']=0
        tile=(null,0,0)

        possible_choices=self.chooseBestTileToPlay()
        if(possible_choices!=[]):
            tile=random.choice(possible_choices)

        if (tile[0]['data']!=0):
            self.tilePlayed=tile[0] 
            inverted=""
            if(tile[2]==1):
                inverted="yes"
            else:
                inverted="no"

            hand="Tile:"+str(self.jsonToDomino(tile[0])) + "," + " Board side:" + tile[1]+"," + "Inverted:" + inverted
            print("\nYou choosed :(" + hand+")")

        else:
            print("You don't have a tile to play")

                                                
        self.send_data(json.dumps(tile))

   
                    

    def chooseBestTileToPlay(self):
        possible_choices=[]
        cheat_prob=random.randint(1,100)
        print("\nProbability to cheat=" + str(cheat_prob))
        if(self.board!=[]):
            #probability to cheat
            begin=self.jsonToDomino(self.board[0])
            end=self.jsonToDomino(self.board[-1])
            #plays with the cheating deck ( saved in a file )
            if(cheat_prob<=self.maximProbCheater):
                #print("I am going to cheat!!")
                possible_choices=self.playTile(begin,end,self.deck_to_cheat)
                self.cheaterFlag=True
                self.currentPl_cheated=True
            #plays only with his deck
            else:
                possible_choices=self.playTile(begin,end,self.player_hand)
                #self.cheaterFlag=False
                #self.currentPl_cheated=False


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
        
        if(self.tilePlayed in self.player_hand):
            self.player_hand.remove(self.tilePlayed)
        
        self.send_data("2O0-OK")
        
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
        #print(self.data,end='')
        message=random.choice(['l','r'])
        self.send_data(str(message)) 
        print(message)
   
    #choose tile direction
    def chooseTileDir(self):
        
        print(self.data,end='')
        message=random.choice([0,1])
        self.send_data(str(message)) 
        print(message)


    def printTiles(self,data,printType):
        #if printType="board" should not include "count"
        count=0
        hand='['

         
        for d in data:
           # print(d)
            if(printType=="board"):
                hand+=str(self.jsonToDomino(d)) + ' | ' 
            elif(printType=="pseudonym"):
                hand+=str(d['index'])+ ":" +str(d['data'])+' | '
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
                else:#list of dominos
                    tile=domino(d['data']['bottom'],d['data']['top'])

                new_data.append(tile)
        
        return new_data

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
        
        if(self.cc_disabler==0):
            self.s.send(signCC(self.username))
            print("Signature sent!")
        else:
            self.send_data("CC Disabled")

        self.msgtoClient.send_data(self.s, "player_hand",self.player_hand, True, self.session_key,integrityKey = self.session_key)
        points = self.msgtoClient.receive_input(self.s, 1024, True, self.session_key,integrityKey = self.session_key)
        print("Player "+ self.username + " had :"+ str(points))
        self.send_data("200-Ok")
    
    def readTilesinFile(self):
        f=open("dominoTiles.txt","r")
        domino_tiles=[]
        while(f.readline()):
            domino_tiles.append(json.loads(f.readline()))
            #f.read(json.loads(data))
            #f.write("\n")
        
        f.close()
        return domino_tiles

     #check if there are cheaters in game:
    # cheaters can be players that played a tile that belongs to current user 
    # play a tile that is already in board  
    def checkForCheaters(self):

        print("\nChecking for cheaters...")
        
        #print(self.board)
        #print(self.player_hand)
        cheater_caught=False
        #list that contains repeated moves 
        cheaters_moves=""
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
                    #self.printTiles(self.player_hand,"player_hand")
                    print("Equal tile is:" + str(domino_tile))
                    cheater_caught=True
                    return cheater_caught,tile
            
        return cheater_caught,cheaters_moves
    
    #Check players Bit commtiment:
    def checkBitCommitment(self):

        cheatersList=list()
        for addrCommit in self.players_commit:
            commit=self.players_commit.get(addrCommit)
            
            if "R2" in commit.keys() and "T" in commit.keys():
                b,R1,R2,T=commit["b"],commit["R1"],commit["R2"],commit["T"]
                flag_commit=check_commit(T,R1,R2,b) #check if BC is generated correctly
                #if false Cheater founded !!
                #print("FLAG=="+str(flag_commit))
                if(not flag_commit):
                    cheatersList.append(addrCommit)
        
        return cheatersList

    #generate commit
    def commit_generation(self,R1=None,R2=None,forged_hand=None):
        dataTiles={}
        
        if(R1==None and R2==None and forged_hand==None):
            dataTiles=self.player_hand.copy()
            R1,R2,b=bit_commitment(dataTiles)
            print("Commiting my hand ...\n")
        else:
            dataTiles=forged_hand.copy()
            R1,R2,b=bit_commitment(dataTiles,R1,R2)
            print("Commiting my hand ...\n")

        if check_commit(dataTiles,R1,R2,b):
            print("Commit created sucessfully\n")
            self.commitment={"Tiles": dataTiles, "commit": b, "R1" : R1, "R2": R2}
            #print("Player full commit is :" +str(self.commitment)+"\n")
            return True
        else:
            print("Bit commitment generation failed!")
            return False
   
    #publish first commit (R1,b)
    #publish second commit (R2,T)
    def publish_Commit(self,cmtype):
        #commit type can be 1 ->first commit 
        #                   2 -> second commit 
        commit=""

        if(cmtype==1): 
            commit=self.commitment["R1"],self.commitment["commit"]
            print("Publishing first commit...")
            #print("Publishing first commit:" + str(commit))
        elif(cmtype==2):
            #part of second type of hiding cheating tiles 
            
            if(self.cheaterFlag and self.currentPl_cheated):
                #If probability <10 than playerforged T
                forged_handProb=random.randint(1,100)

                #else player don't forged T 
                #print("forged_handProb=" + str(forged_handProb))
                if(forged_handProb<=10):
                    print("Last Tile played is " + str(self.tilePlayed))
                    #begin_hand
                    #print(self.commitment)
                    forged_hand= self.commitment["Tiles"].copy()
                    encryptTile=assymetric_encript(self.public_key,str(self.tilePlayed).encode())
                    forged_hand.append(encryptTile)
                    self.commit_generation(self.commitment["R1"],self.commitment["R2"],forged_hand)
                
                commit=self.commitment["R2"],self.commitment["Tiles"]
                print("Publishing second commit...")


            else:
                commit=self.commitment["R2"],self.commitment["Tiles"]
                print("Publishing second commit...")

               # print("Publishing second commit:" + str(commit))

           
        self.msgtoClient.send_data(self.s, "commit", str(commit), integrityKey = self.session_key)
    


    def printMoves(self):
        for move in self.gameRegister:
            # username_moves=dict(self.gameRegister[addr])
            # moves =list(username_moves.values())
            for addr,username in move:
                #print(addr)
                #print(username)
                data=move[(addr,username)]
                tile,side,inverted=data[0],data[1],data[2]
                # print("Tile="+str(tile))
                move_local=""
                if(tile["index"]!=-1):
                    domino_tile=self.jsonToDomino(tile)
                    if(inverted==1):
                        domino_tile.invertTile()
                    if(side=="r"):
                        move_local="right"
                    else:
                        move_local="left"
                    print("Addr:"+str(addr) +" with username " +str(username)+ " played " + str(domino_tile) +" in "+ move_local  )

                else:
                    domino_tile="nothing"
                    print("Addr:"+str(addr) +" with username " +str(username)+ " played " + str(domino_tile))
    

    #when server reveals susp 
    #check who is the susp
    def findSuspRevealed(self,addr,forgedTile,suspTile):

        if(not forgedTile.equalTile(suspTile)):
            if(addr not in self.cheatersList):
                self.cheatersList.append(addr)

        elif(forgedTile.equalTile(suspTile)):
            if(addr not in self.cleanList):
                self.cleanList.append(addr)
                              
        #print("Current suspicious list is:" +str(self.cleanList))
        #print("Current cheaters list is:" +str(self.cheatersList))

#functions to check if there was someone cheating: 
#asks for commit2 and then check_commitment 
# if true than it means the player didn't cheat 
# otherwise the player has cheated 
#
if __name__ == "__main__":
    main()