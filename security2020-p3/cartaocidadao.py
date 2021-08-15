from PyKCS11 import *
import sys
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from OpenSSL.crypto import load_certificate, load_crl, FILETYPE_ASN1, FILETYPE_PEM, Error, X509Store, X509StoreContext,\
    X509StoreFlags, X509StoreContextError

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import *
from cryptography import x509

operatingSystem=1

def initPkcs():
    if(operatingSystem==1):
        lib = '/usr/local/lib/libpteidpkcs11.dylib' #MacOS
    else:
        lib = '/usr/local/lib/libpteidpkcs11.so' #Linux
    try:
        pkcs11 = PyKCS11Lib()
        pkcs11.load(lib)
    except PyKCS11Error:
        Exception("Error loading the lib")
        exit(10)
    else:
        try:
            # listing all card slots
            slots = pkcs11.getSlotList()
            if len(slots) < 1:
                print("\nERROR: No card reader detected!")
                raise Exception()
            return pkcs11.openSession(slots[0])
        except PyKCS11Error:
            print("Couldn't open the session")
            exit(10)
        except:
            print("No card detected!")
            exit(11)

def login():
    pin = None
    while True:
        pin = input('PIN: ') 
        try:
            initPkcs().login(pin)
        except PyKCS11Error:
            print("\nERROR: Pin Incorrect")
            return False
        else:
            return True

def getId():
    info = initPkcs().findObjects(template=([(PyKCS11.CKA_LABEL, "CITIZEN AUTHENTICATION CERTIFICATE"),
                                                            (PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE)]))

    infos = ''.join(chr(c) for c in [c.to_dict()['CKA_SUBJECT'] for c in info][0])

    names = infos.split("BI")[1].split("\x0c")
    return ' '.join(names[i] for i in range(1, len(names)))

def getBI():
    info = initPkcs().findObjects(template=([(PyKCS11.CKA_LABEL, "CITIZEN AUTHENTICATION CERTIFICATE"),
                                                            (PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE)]))

    infos = ''.join(chr(c) for c in [c.to_dict()['CKA_SUBJECT'] for c in info][0])

    bi = infos.split("BI")[1][:8]
    return bi

def getCerts():
    info = initPkcs().findObjects(template=([(PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE), (PyKCS11.CKA_LABEL, "CITIZEN AUTHENTICATION CERTIFICATE")]))
    der = bytes([c.to_dict()['CKA_VALUE'] for c in info][0])
    # converting DER format to x509 certificate
    cert = x509.load_der_x509_certificate(der, default_backend()).public_bytes(Encoding.PEM)
    return cert   


def signCC(message):
    privateKey = initPkcs().findObjects(template=([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),(PyKCS11.CKA_LABEL, "CITIZEN AUTHENTICATION KEY")]))[0]
    signedlist = initPkcs().sign(privateKey, message.encode(), Mechanism(PyKCS11.CKM_SHA256_RSA_PKCS, ""))
    return bytes(signedlist)

def verifySign(cert, data, signature):
    cert = x509.load_pem_x509_certificate(cert, default_backend())
    publicKey = cert.public_key()
    paddingv = padding.PKCS1v15()
    print("####################")
    try:
        state = publicKey.verify(
            signature,
            bytes(data.encode()),
            paddingv,
            hashes.SHA256(),
        )
        return True
    except:
        return False

if __name__ == '__main__':

    print(getId())
    print(getBI())

    #login()

    datatobeSigned = "istoeumteste"
    signedData = signCC(datatobeSigned)
    print("Sign Test")
    verifySign(getCerts(), datatobeSigned, signedData)