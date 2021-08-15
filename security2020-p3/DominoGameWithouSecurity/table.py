import collections
import  random
import json
from domino import *

class Table(): 
    def __init__(self):
        self.domino_tiles=self.createPieces()
    
        self.domino_tilesJSON=self.parseTilesToJson(self.domino_tiles)
        self.writeTilesinFile(self.domino_tilesJSON)
        random.shuffle(self.domino_tilesJSON)
        self.board = list()
        self.pseudonymTiles={}


    def createPieces(self):
        domino_tiles=[]

        for i in range(0,7):
            for j in range(0,7):
                new_domino=domino(i,j)
                if (not self.containsPiece(domino_tiles,new_domino)):
                    index=random.randint(0,1000000) #creates a random index
                    while(not self.checkIndexExists(index,domino_tiles)):
                        index=random.randint(0,1000000)
                    
                    value_tuple=(index,new_domino)
                  #  print(value_tuple)
                   # self.addPseudonymTile(index,new_domino)
                    domino_tiles.append(value_tuple)

                #print(new_domino.print())
        return domino_tiles
    
    def getTilesJson(self):
        return self.domino_tiles
    #check if the random index already exist in the list
    def checkIndexExists(self,idx,tiles_list):
        
        for index,tile in tiles_list:
            if (idx==index):
                return False

        return True 

    #checks if the deck contains the domino piece
    def containsPiece(self,domino_tiles,tile):
        
        for i,d in domino_tiles:
            if (d.equalTile(tile)):
                return True
        return False

    def printTiles(self,domino_tiles):
        
        string="["
        for d in domino_tiles:
            string+=str(d)+","
        string+="]"
        return string
    
    def parseTilesToJson(self,tiles):
        domino_tilesJSON=[]
        for i,d in tiles:
            data={}
            data['index']=i
            data['data']=d.data
            print(data)
            domino_tilesJSON.append(data)

        return domino_tilesJSON

    def get_hands(self):
        return self.hands

    def left_edge(self):
        return self.board[0]
    
    def right_edge(self):
        return self.board[-1]
    

    #goal here is to retrieve a pseudonym giving a (index,tile)
    def addPseudonymTile(self,index,tile):
       
     #   key=hash(tile)
        print(key)
        pseuDonym=hash((index,tile))
        print(pseuDonym)
        
    
        return pseuDonym
    #goal here is to retrieve a pseudonym giving a (index,tile)
    #def getTileFromPseudonym(self):

    def __hash__(self,tile):
        print('The hash is:')
        return hash(tile)


    def isValidPlay(self, direction, tile):
        if len(self.board)==0:
            return True

        if(direction=="r"):
            if(tile['data']['top']==self.right_edge()['data']['bottom']):
                return True
        else:
            if(tile['data']['bottom']==self.left_edge()['data']['top']):
                return True
        
        return False
    
    def writeTilesinFile(self,domino_tiles):
        f=open("dominoTiles.txt","w")
        for data in domino_tiles:
            f.write(json.dumps(data))
            f.write("\n")
        f.close()


        