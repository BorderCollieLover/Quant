#this is a utility file that allows us to perform simple tasks such as I/O, disk writing etc
#we use a pickle object. This is like, just preserving a Python object in your disk.

#python3 -m pip instal pickle

import pickle

def save_file(path, object):
    try:
        with open(path, "wb") as fp:
            pickle.dump(object, fp)
    except Exception as err:
        print("pickle error: ", str(err))

def load_file(path):
    try:
        with open(path, "rb") as fp:
            file = pickle.load(fp)
        return file
    except Exception as err:
        print("load error: ", err)
    