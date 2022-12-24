from photoAlbum import album
import pandas as pd
import itertools
def build_with(name,filename):
    album_dict = pd.read_excel(filename,sheet_name=None,header=None)
    return rename(name,album_dict)

def rename(name, album_dict:dict):
    if(len(album_dict)==1):
        return dict(zip( (name), album_dict.values()))
    names = (name + " " + str(index) for index in range(1,len(album_dict)+1))
    return dict(zip(names,album_dict.values()))

def build_with_dict(name,filename):
    return album(build_with(name,filename))