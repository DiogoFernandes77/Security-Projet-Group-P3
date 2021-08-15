import os
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography . hazmat . primitives . asymmetric import rsa
from cryptography . hazmat . primitives import serialization
from cryptography . hazmat . backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

#assymetric encription ----------------------------------------------------------

def assymetric_key_generator(key_size = 2048):

    priv_key = rsa . generate_private_key ( 65537 , key_size , default_backend () )
    return priv_key


def assymetric_encript(pubkey,message):
    
    ciphertext = pubkey.encrypt ( message , padding . OAEP ( padding . MGF1 ( hashes . SHA256 () ) , hashes . SHA256 () , None ) )
   
    return ciphertext


def assymetric_decrypt(privkey,ciphertext):
    
    plaintext = privkey.decrypt ( ciphertext ,
    padding . OAEP ( padding . MGF1 ( hashes . SHA256 () ) ,
    hashes . SHA256 () , None ) )
    
        
    return plaintext


def signing(privkey):#user authentication
    try:
        auth_msg = b'Esta mensagem serve para authenticar'
        signature = privkey.sign(auth_msg,padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())
    except:#signing failed
        return False
    return signature

def verification(pubkey,signature):
    auth_msg = b'Esta mensagem serve para authenticar'
    
    try:
        pubkey.verify(signature, auth_msg,padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH),hashes.SHA256())

    except : #authentication failed
        return False
    else:
        return True

def testing_assymetric():
    priv_key = assymetric_key_generator()
    k = priv_key.private_bytes(serialization . Encoding . PEM, serialization.PrivateFormat.TraditionalOpenSSL,serialization.NoEncryption())
    
    o = serialization.load_pem_private_key(k,None,default_backend())
    
    # sig = signing(priv_key)
    # print('signature' + str(sig))
    # pub_key = priv_key.public_key()
    # print(verification(pub_key,sig))
    
    # # ------------encrypt decrypth test----------
    # cipher = assymetric_encript(priv_key.public_key(),b'mensagem de teste')
    # print(cipher)
    # plaintext  = assymetric_decrypt(priv_key,cipher)
    # print(plaintext)


#testing_assymetric()