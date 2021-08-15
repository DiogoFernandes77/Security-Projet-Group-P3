import hashlib
import os
import sys

#Commitment
#basically to check if someone has cheated the hash must be equal 
def bit_commitment(data, R1=None, R2=None):
    
    if R1 == None or R2 == None:
        R1=os.urandom(32)
        R2=os.urandom(32)

    #print("R1="+str(R1))
    #print("R2="+str(R2))
    #print("\nPLAYER HAND IS:"+str(data))
    
    h = hashlib.md5()
    tiles=data.copy()
    tiles.append(R1)
    tiles.append(R2)
    tiles=bytes(str(tiles),"utf-8")
    # tiles+=R1 +R2
    
    #print("Tiles= " + str(tiles))
    h.update(tiles)
    key=h.hexdigest()
    #print("Key="+key)
    
    return(R1,R2,key)
    #print((R1,R2,key))

            

#check if the commitment was well generated
def check_commit(data,R1,R2,commit):
    #calculate the commit given original tiles data
    r1,r2,temp_commit=bit_commitment(data,R1,R2)
    #if legit commit must be equal 
    #otherwise commit is not legal
    return temp_commit==commit
