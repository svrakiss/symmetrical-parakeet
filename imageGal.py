from ast import ExtSlice
from io import BytesIO
from PIL import Image
import pyodbc
import requests
import os
import shutil
import mimetypes
# import rename_illegal_filenames
# print ([x for x in pyodbc.drivers() if x.startswith('Microsoft Access Driver')])

# -*- encoding: utf-8 -*-
#
# Author: Massimo Menichinelli
# Homepage: http://www.openp2pdesign.org
# License: MIT
#

import string
# import os

# Adapted from: http://www.andrew-seaford.co.uk/generate-safe-filenames-using-python/
## Make a file name that only contains safe charaters  
# @param inputFilename A filename containing illegal characters  
# @return A filename containing only safe characters  
def makeSafeFilename(inputFilename):
    # Set here the valid chars
    safechars = string.ascii_letters + string.digits + "~ -_.();[]"
    try:
        return filter(lambda c: c in safechars, inputFilename)
    except:
        return ""
    pass  

conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    r'DBQ=C:\Users\danny\OneDrive\Documents\code\Koikatsu Mr D\Database1.accdb;'
    )
cnxn = pyodbc.connect(conn_str)
crsr = cnxn.cursor()
def clean_char_name(fn):
    fn= fn.replace("\\","-")
    fn=fn.replace("/","-")
    fn=fn.replace("//","-")
    fn = fn.replace(".","_")
    fn = makeSafeFilename(fn)
    fn = ''.join([x for x in fn])
    return fn

def make_photo_folder(rows, folder_name='Anime'):
    os.makedirs(os.path.abspath(folder_name),exist_ok=True)
    for row in rows:
        if(row.Pics == None):
            continue
        data = requests.get(row.Pics.strip('#'))
        fn = row.Characters
        content_type = data.headers['content-type']
        #
        ext = mimetypes.guess_extension(content_type)
        if(ext==None):
            ext = ".png"
            # print(ext)
        fn = clean_char_name(fn) + ext

        im = Image.open(BytesIO(data.content))
        if(".gif" in fn):
            im.save(fn,save_all=True)
        else:
            im.save(fn)
        src_path= os.path.abspath(fn)
        dest_path=os.path.abspath(folder_name+os.sep+fn)
        shutil.move(src_path,dest_path)
        # return data

helper = lambda x: make_photo_folder(crsr.execute("SELECT Characters, Pics FROM Images INNER JOIN Hoja2 ON Images.Characters = Hoja2.%s WHERE Pics IS NOT NULL" % x),x) 

categories = ['Anime','Deluxe','Not-so-Human','Videogames','Movies','Comics','Cartoons']