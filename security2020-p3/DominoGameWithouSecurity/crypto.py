import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac


def encrypt(message, secretkey):
    
    iv = os.urandom ( algorithms.AES.block_size // 8 )
    cipher = Cipher ( algorithms.AES( secretkey ) , modes.CBC ( iv ),default_backend())
    encryptor = cipher.encryptor ()
    padder = padding.PKCS7( algorithms.AES.block_size ).padder()
  
    ciphertext = encryptor.update(padder.update(message) + padder.finalize()) + encryptor.finalize()
    
    #iv colocado na mensagem para depois decifrar,"They do not need to be kept secret and they can be included in a transmitted message" 
    return [ciphertext,iv] 
        

def decrypt(ciphertext, secretkey):
    #ciphertext = [msg_cifrada,iv(initialization_vector)]
    iv = ciphertext[1]
    
    cipher = Cipher(algorithms.AES(secretkey), modes.CBC(iv), default_backend())
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7( algorithms.AES.block_size ).unpadder()

    #para decifrar a ordem troca, o unpadder é so no fim
    message_padded = decryptor.update(ciphertext[0])
    message = unpadder.update(message_padded)
    
    
    return message

def secretkey(word):
    
    salt = b'\ x00 '
    kdf = PBKDF2HMAC( hashes . SHA1 () , 16 , salt , 1000 , default_backend () )
    key = kdf.derive( bytes( word , 'UTF -8 ' ) )
    return key


def testing():
    msg = b'mensagem secreta'
    key = secretkey('palavra_secreta')
    cipher_message = encrypt(msg,key)
    print('mensagem cifrada='+ str(cipher_message[0]))
    message = decrypt(cipher_message,key)
    print('mensagem decifrada=' + str(message))


#testing()