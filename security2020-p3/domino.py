import json


class domino:
    
    def __init__(self,bottom,top):
        self.top=top
        self.bottom=bottom
        self.data = {}
        self.data['top'] = self.top
        self.data['bottom'] = self.bottom
        
    
    def setTop(self,number):
        if (number >6):
            print("[ERROR]-Invalid number")
        else:
            self.top=number
    
    def setBottom(self,number):
        if (number >6):
            print("[ERROR]-Invalid number")
        else:
            self.top=number
    
    def getTop(self):
        return self.top
    
    def getBottom(self):
        return self.bottom

    def toJson(self): #serialize to json
        return json.dumps(self, default=lambda o: o.__dict__)
    
    def equalTile(self,d2):
        if(self.top==d2.top and self.bottom==d2.bottom or (d2.top==self.bottom and d2.bottom==self.top)):
            return True
        else:
            return False

    def invertTile(self):
        tmpTop=self.top
        tmpBottom=self.bottom
        self.top=tmpBottom
        self.bottom=tmpTop

        self.data['top'],self.data['bottom']  = self.top, self.bottom
    
    def printInvertTile(self):
        return "["+ str(self.bottom)+ "-"+str(self.top) +"]"
    
    def __str__(self):
        return "["+ str(self.top)+ "-"+str(self.bottom) +"]"