import pickle
from symetric_functions import *
from cryptography.hazmat.primitives import hashes, hmac

def sign_message(message, key):
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(pickle.dumps(message))
    return h.finalize()

def verify_message(message, key, signature):
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(pickle.dumps(message))
    valid = True
    try:
        h.verify(signature)
    except Exception as e:
        valid = False
        print("Invalid signature. - ", e)
    return valid



#key = secretkey(word_generator())
#hmac1 = sign_message(b'12341', key)
#print("HMAC")
#print(verify_message(b'12341', key, hmac1))