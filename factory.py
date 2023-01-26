from photoAlbum import album
import pandas as pd
import itertools
import numpy as np
import math
class Builder:
    my_album:album
    should_split=False
    name = None
    source = None
    chunk = None
    filename=None
    # the methods should all return a builder to allow fluent-style chaining
    def with_file(self,filename):
        self.with_source("file")
        self.filename=filename
        return self
    def with_source(self,source):
        self.source=source
        return self
    def with_name(self,name):
        self.name=name
        return self
    def split(self,chunk=None):
        # chunk will be half the size of the current album by default
        if chunk is not None:
            # should i defer building until the actual build step? sounds better
            self.chunk = chunk
        self.should_split = True
        return self
    def build(self):
        if self.source is None or self.source == "file":
            album_dict = pd.read_excel(self.filename,sheet_name=None,header=None)
            if self.should_split:
                album_dict = split(album_dict=album_dict,chunk=self.chunk)
            if self.name is not None:
                album_dict =rename(self.name,album_dict)
            self.my_album= album(album_dict)
            return self.my_album

        return None
def split(album_dict:dict[int | str , pd.DataFrame],chunk=None):
    my_chunk = lambda x: chunk if chunk is not None and len(x) > chunk else int(len(x)/2)
    splitter = lambda x: (x.iloc[my_chunk(x):], x.iloc[:my_chunk(x)])
    other_splitter = lambda x: np.array_split(x,math.ceil(len(x)/my_chunk(x)))
    result = {}
    for v in album_dict:
        sub_frames :list[pd.DataFrame] =other_splitter(album_dict.get(v))
        # now we have to reset the index
        
        sub_frames = [x.reset_index(drop=True) for x in sub_frames]
        # print(splitter(album_dict.get(v)))
        names = (v + " " + str(index) for index in range(1,len(sub_frames)+1))
                # type: ignore   
        result.update(dict(zip(names,sub_frames)))
    return result


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