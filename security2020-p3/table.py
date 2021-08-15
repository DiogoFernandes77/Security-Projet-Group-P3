import collections
import  random
from domino import *
import hashlib

class Table(): 
    def __init__(self):
        self.domino_tiles=self.createPieces()
        self.pseudonymTiles={}

        self.domino_tilesJSON=self.parseTilesToJson(self.domino_tiles)
        self.writeTilesinFile(self.domino_tilesJSON)
        self.domino_tilesJSON=self.parseTileToPseudonym(self.domino_tilesJSON)
        random.shuffle(self.domino_tilesJSON)
        self.board = list()
    


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
           # print(data)
            domino_tilesJSON.append(data)

        return domino_tilesJSON
    
    def parseTileToPseudonym(self,tiles):
        domino_tilesJSON=[]
        for d in tiles:
            data={}
            #print("i="+ str(d["index"]))
            #print("d=" + str(d["data"]))
            pseudonym=self.addPseudonymTile(d["index"],d["data"])
            data['index']=d["index"]
            data['data']=pseudonym
           # print(data)
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
       
        #key genereation
        h = hashlib.md5()
        h.update(bytes(json.dumps(tile),encoding="utf8"))
        key=h.hexdigest()
        #print("Key is =" + key)

        #pseudonym generation
        h2=hashlib.sha1()
        h2.update(bytes(json.dumps((index,key,tile)),encoding="utf8"))
        pseuDonym=h2.hexdigest()
        
        while(not self.checkPseudonymExists(pseuDonym)):
            h2=hashlib.sha1()
            h2.update(bytes(json.dumps((index,key,tile)),encoding="utf8"))
            pseuDonym=h2.hexdigest()
        
        self.pseudonymTiles.update({pseuDonym:{key:(index,tile)}})

        return pseuDonym


    #goal here is to retrieve a tile giving pseudonym
    def getTileFromPseudonym(self,pseudonym):
        #print(self.pseudonymTiles)

        pseudonym_dict=self.pseudonymTiles.get(pseudonym)

        key=list(pseudonym_dict.keys())[0]
        #print(key)

        tile=pseudonym_dict.get(key)
        #(index,tile)
        
        return tile[0],tile[1],key
    
    def checkPseudonymExists(self,pseudonym):
       
        for p in self.pseudonymTiles:
            if p==pseudonym:
                return False
        return True

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