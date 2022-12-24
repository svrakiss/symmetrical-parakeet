from email.mime import image
from functools import singledispatch
import itertools
import re
import sys
import json
from uuid import NAMESPACE_URL
import requests
from Google import Create_Service
import pandas as pd
import pickle
import os
import numpy as np
import glob
import math
from typing import Any, Iterable, Optional
import re
from imageGal import *
import mimetypes
import pyperclip as pp
from github_imports.profile import profile
def upload(token, file:str,name:str = 'None'):
    f = open(file, 'rb').read();
    if(name == 'None'):
        name =  os.path.basename(file)
    return upload1(token,f, name = name)

def upload1(token, f:bytes,name:str)->bytes:
    url = 'https://photoslibrary.googleapis.com/v1/uploads'
    headers = {
        'Authorization': "Bearer " + token,
        'Content-Type': 'application/octet-stream',
        'X-Goog-Upload-File-Name': name,
        'X-Goog-Upload-Protocol': "raw",
    }

    r = requests.post(url, data=f, headers=headers)
    # print ('\nUpload token: %s' % r.content)
    return r.content


def uploadDownload(url,token, name=None)->bytes:
    stuff = requests.get(url)
    if(name is None):
        name = stuff.headers['content-disposition']
        name = re.findall("filename=(.+)",name)[0]
    content_type = stuff.headers['content-type']
        #
    ext = mimetypes.guess_extension(content_type)
    if(ext==None):
        ext = ".png"

    upload_token=upload1(token,f=stuff.content,name=name+ext)
    return upload_token

def createItem(token, upload_token, albumId):
    url = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'

    body = {
        'newMediaItems' : [
            {
                "description": "test upload",
                "simpleMediaItem": {
                    "uploadToken": upload_token
                }  
            }
        ]
    }

    if albumId is not None:
        body['albumId'] = albumId;

    bodySerialized = json.dumps(body);
    headers = {
        'Authorization': "Bearer " + token,
        'Content-Type': 'application/json',
    }

    r = requests.post(url, data=bodySerialized, headers=headers)
    print ('\nCreate item response: %s' % r.content)
    return r.content

# authenticate user and build service
f=open('albumStuff.json')
r=json.load(f)
CLIENTS_SECRETS_FILE=r"..\..\..\..\Downloads\client_secret_960010643863-uavuuusnu06s5r3d69cjkalh0nt5jftn.apps.googleusercontent.com.json"
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.sharing','https://www.googleapis.com/auth/photoslibrary.appendonly']
API_SERVICE_NAME = 'photoslibrary'
API_VERSION = 'v1'
CHUNK_SIZE = 50


RESULTS_FILE= r".\pastResults.json"

def pickle_load_token(pickle_name='token_photoslibrary_v1.pickle'):
    if(os.path.exists(pickle_name)):
        token = pickle.load(open(pickle_name, 'rb'))
        if token.expired:
            os.remove(pickle_name)
    service = Create_Service(CLIENTS_SECRETS_FILE,API_SERVICE_NAME,API_VERSION,SCOPES) # throws an error if token file  is expired
    token = pickle.load(open(pickle_name, 'rb'))
    while(token.expired):
        os.remove(pickle_name)
        service = Create_Service(CLIENTS_SECRETS_FILE,API_SERVICE_NAME,API_VERSION,SCOPES)
        token = pickle.load(open(pickle_name, 'rb'))
    return token, service
token, service = pickle_load_token()

def look_at_all(folder_name,token):
    files = glob.glob(os.path.join(folder_name,"*"))
    # result = np.empty(len(files))
    # i=0
    result =[]
    for x in files:
        upload_token = upload(token, file=x, name=None)
        result.append(upload_token.decode('utf-8'))
        # i=i+1
        # return result
    return result


def make_items(service,tokens, albumId,descriptions=None, cmd=None,relative_id=None)->list[dict[str,list]]:
    # if(len(tokens)>50):
    tokens_list=np.array_split(tokens,math.ceil(len(tokens)/CHUNK_SIZE));
    if(descriptions is not None):
        descriptions_list = np.array_split(descriptions,math.ceil(len(tokens)/CHUNK_SIZE)); # if these aren't the same length an error will be thrown by zip()
    upload_response = []
    for i in range(len(tokens_list)):
        if descriptions is not None:
            new_media_items = [{'description':d,'simpleMediaItem':{'uploadToken':tok }} for tok, d in zip(tokens_list[i], descriptions_list[i])]
        else:
            new_media_items = [{'simpleMediaItem':{'uploadToken':tok }} for tok in tokens_list[i]];

        request_body = {'newMediaItems':new_media_items}
        request_body['albumId']=albumId
        if(cmd is not None):
            # this will allow you to input incorrect syntax
            # cmd should be AFTER MEDIA ITEM
            if relative_id is not None:
                request_body['albumPosition'] = {
                    'position':cmd,
                    'relativeMediaItemId':relative_id
                }
            else:
                # cmd should be 
                request_body['albumPosition']={
                    'position':cmd
                }
        upload_response.append(service.mediaItems().batchCreate(body = request_body).execute())
    return upload_response


def make_album(service, albumName, request_body=r):
    request_body['create']['album']['title'] = albumName
    return service.albums().create(body=request_body['create']).execute()


@singledispatch
def validate_names(filename:str):
# TODO test for duplicate removal
    albumDict = pd.read_excel(filename,sheet_name=None,header=None) # All Sheets in a dict sheetname:dataframe
    for x in albumDict:
        for i in range(len(albumDict[x])): # doesn't make any assumptions about column name. just iterates over the first column
            # easily replaced with albumDict[x][albumDict[x].columns[0]] which should return a list
            if crsr.execute("SELECT 1 FROM Images WHERE Characters=?",albumDict[x].iat[i,0]).fetchone() is None:
                print(albumDict[x].iat[i,0])
    return {x:albumDict[x].drop_duplicates(subset=albumDict[x].columns[0]) for x in albumDict}

@validate_names.register
def _(albumDict:dict):
    for x in albumDict:
        for i in range(len(albumDict[x])): # doesn't make any assumptions about column name. just iterates over the first column
            # easily replaced with albumDict[x][albumDict[x].columns[0]] which should return a list
            if crsr.execute("SELECT 1 FROM Images WHERE Characters=?",albumDict[x].iat[i,0]).fetchone() is None:
                print(albumDict[x].iat[i,0])
    return {x:albumDict[x].drop_duplicates(subset=albumDict[x].columns[0]) for x in albumDict}

def get_pics(albumDict, token=token):
# TODO test for same name in different albums (don't upload more than once)
    resultArray={}
    for x in albumDict:
        for i in range(len(albumDict[x])):
            if albumDict[x].iat[i,0] in resultArray:
                continue;
            url=crsr.execute("SELECT Pics FROM Images WHERE Characters=?",albumDict[x].iat[i,0]).fetchone()[0]
            upload_token = uploadDownload(url.strip('#'),token=token.token,name = clean_char_name(albumDict[x].iat[i,0]))
            resultArray[albumDict[x].iat[i,0]]=upload_token.decode('utf-8')
    return {x: [resultArray[y] for y in albumDict[x][albumDict[x].columns[0]] ] for x in albumDict}


def grab_upload_tokens(service, names:dict[int | str, pd.DataFrame], token=token):
    # false means upload album own
    # true (default) means check if the character exists before uploading a photo
    newDict = {}
    resArray=[]
    resultArray=get_pics(names) # upload token array dict
    for x in names:
        res=make_album(service,x)
        newDict[x]=res.get('id')
        result =make_items(service=service,tokens=np.array(resultArray[x]),albumId=res.get('id'))
        resArray.append(result)
        # for i in range(len(names[x])):
            # names[x].iat[i,0]
            # resArray.append()
    return resultArray

def final_step(service, names,tokens,token=token):
    newDict = {}
    resArray=[]
    # resultArray=get_pics(names) # upload token array dict
    for x in names:
        res=make_album(service,x)
        # newDict[x]=res.get('id')
        result =make_items(service=service,tokens=np.array(tokens[x]),albumId=res.get('id'), descriptions= np.array(names[x][names[x].columns[0]]))  # also assumes the column name is 0 ( guaranteed because of the way things are read from the file)
        newDict[x]= result
    return newDict

# Output should be empty if it succeeds
def updateResults(names, service=service, token=token, results=RESULTS_FILE):
    f = open(RESULTS_FILE)
    results = json.load(f)
    result = {}
    for x in names:
        res=make_album(service, x)
        body={
            "mediaItemIds":[results[q]['mediaItem']['id'] for q in names[x][0]], # assumes the column name is 0
        }
        result[x] = service.albums().batchAddMediaItems(albumId=res.get('id'), body=body).execute()

    return result 

def update_results(names:dict[int | str, pd.DataFrame], upload_response:dict[str , list], results=RESULTS_FILE):
    # remove names not being added before you call this method
    f = open(results)
    results_json = json.load(f)
    newDict = {}
    funk = lambda x: x['newMediaItemResults']
    # funk2 = lambda x: unpack(x, lambda y: y['mediaItem']['id'])
    # use unpack(names[][], lambda x: funk2(funk(x))  ) to get the ids 
    flatten = itertools.chain.from_iterable
    for x in names:
        col_1 = names[x].columns[0]
        if(len(upload_response[x])==0):
            continue;
        results_json.update(dict(zip(names[x][col_1],  flatten(unpack(upload_response[x],funk))  )))
    
    with open(results,'w') as jsonFile:
        json.dump(results_json,jsonFile,indent=4)

# yes, order is very important. 
def split_album(names, results=RESULTS_FILE)->dict:
    # TODO remove assumptions that first column is named '0'
    # TODO remove json dependency
    f = open(results)
    results_json = json.load(f)
    output = {}
    for p in names:
        indices = [x for x in range(len(names[p])) if names[p][names[p].columns[0]][x] in results_json]
        ind_array=[]
        output[p]={'indices':indices}
        for q in range(len(indices)):
            if (indices[q]==0):  # q == 0 right now btw
                if(len(indices)>1):
                    if(indices[q+1]!=1):
                        ind_array.append({'cmd':'AFTER_MEDIA_ITEM', 'id': results_json[names[p][0][0]]['mediaItem']['id'], 'slice': slice(1,indices[q+1])});  # normally would be slice(q+1, indices[q+1])
                    continue;
                else:
                    if len(names[p]==1):
                        break
                    ind_array.append({'cmd':'AFTER_MEDIA_ITEM', 'id': results_json[names[p][0][0]]['mediaItem']['id'], 'slice': slice(1,len(names[p]))});  # error if len(names[p]) == 1
                    continue;
            elif q==0:
                # pick up what's behind you
                ind_array.append({'cmd':'FIRST_IN_ALBUM','slice': slice(0,indices[q])});
            if q==len(indices)-1:
                # last index in the list
                # could also be last index in the names list too
                if(indices[q]==len(names[p])-1):
                    break
                ind_array.append({'cmd':'LAST_IN_ALBUM','slice':slice(indices[q]+1,len(names[p]))})
            else:
                if indices[q]+1==indices[q+1]:
                    continue;
                ind_array.append({'cmd':'AFTER_MEDIA_ITEM', 'id': results_json[names[p][names[p].columns[0]][indices[q]]]['mediaItem']['id'], 'slice': slice(indices[q]+1,indices[q+1])});
        output[p]['ind_array']=ind_array
    return output

def new_items(names : dict [ int| str, pd.DataFrame], sets:dict[int | str , dict], token=token):
    # this first version is for assuming all of the items are unrelated: i.e. names chars can be in multiple albums and they
    # will be uploaded more than once.
    # decided to implement this in get_pics()
    # so this shouldn't be a problem anymore

    # get_pics() doesn't have to be called on individual slices
    # it is usually called on the entire album Dict

    tokens = get_pics({x:names[x].drop(sets[x]['indices']) for x in names},token)  # just looking at the rows that are new

    # since these are guaranteed to be unique, you can upload them all

    # TODO figure out dispatch and change the method name to get_pics

    return tokens

def make_both(names, sets, tokens, service=service,token=token, results=RESULTS_FILE):
    # TODO remove json dependency
    result = {}
    albumIds = []
    f = open(results)
    results = json.load(f)  # should probably change the name of this 
    for x in names:
        res=make_album(service, x)
        albumIds.append(res.get('id'))
        if len(sets[x]['indices'])!=0:
            body={
                "mediaItemIds":[results[q]['mediaItem']['id'] for q in names[x][names[x].columns[0]][sets[x]['indices']]], # assumes the column name is 0
            }
            service.albums().batchAddMediaItems(albumId=res.get('id'), body=body).execute()
        else: # len(ind_array) == 0 for the wrong reason
            result[x] = make_items(service,tokens[x], res.get('id'),names[x][names[x].columns[0]])
            continue;
        tokens_i_need = dict(zip(names[x][names[x].columns[0]].drop(sets[x]['indices']),tokens[x]))   # this is undesirable, there should be a way to do this without reconstruction
        result[x] = []
        for ind in sets[x]['ind_array']:
            result[x].append(make_items(service,[tokens_i_need[y] for y in names[x][names[x].columns[0]][ind['slice']]],res.get('id'),names[x][names[x].columns[0]][ind['slice']], ind['cmd'], ind.get('id')))
        # the format of result [x]  before returning
        # currently it is [ [ dict ], [dict] ] or [dict]
    return result, albumIds


def unpack(arg:Iterable, func):
    # the base case is the dict in the list of dict 
    if isinstance(arg, dict):
        yield func(arg)
    # isinstance(arg, list) == True
    else:
        for x in arg:
            yield from unpack(x,func)
            # result needs to be an iterable ( you get this for free since generators are iterable)


class album():
    albumDict:dict[int | str, pd.DataFrame]
    sets:dict
    tokens:dict
    service:Any
    token:Any
    albumIds:list
    result:Any
    other_result:Any
    #TODO make another constructor but for scraping from the clipboard
    @singledispatch
    def __init__(self, excelFile:str):
        self.albumDict = validate_names(excelFile)
        self.sets = split_album(self.albumDict)
        self.service=service

    @__init__.register
    def _(self,albumDict:dict):
        self.albumDict = validate_names(albumDict)
        self.sets = split_album(self.albumDict)
        self.service = service

    def make(self):
        self.tokens = new_items(self.albumDict,self.sets)
        if all(len(self.sets[x]['ind_array'])==0 for x in self.sets):
            print("everything is old")
        return make_both(self.albumDict,self.sets,self.tokens)
    def update(self,results=None):
        if(results is None):
            if(self.result is None):
                return;
            results = self.result
        real_dict = { x:self.albumDict[x].drop(self.sets[x]['indices']) for x in self.albumDict}
        update_results(real_dict,results)
    def make_and_share(self):
        # it's important to store intermediate results bc more often than not something will go wrong
        self.result, self.albumIds = self.make()
        return self.share(self.albumIds)
    def share(self, arg:Iterable):
        rip_body = lambda x: {'sharedAlbumOptions': x.get('create').get('album').get('shareInfo').get('sharedAlbumOptions')}
        config = r
        # TODO make this a generator. (replace g.append() with yield )
        g=[]
        for i in arg:
            g.append(self.share_static(self.service,rip_body(config), i))
        return g
    @staticmethod
    def share_static(service,body,id):
        return service.albums().share(body=body,albumId=id).execute()
    def make_and_share_and_rip_info(self):
        key_get = lambda x: x.get('shareInfo').get('shareableUrl')
        self.other_result = self.make_and_share()
        return unpack(self.other_result,key_get)
    def ppcopy(self,arg):
        pp.copy('\n'.join(arg))
    @staticmethod
    @profile(sort_by='cumulative', strip_dirs=True)
    def make_share_copy(sheetName):
        temp = album(sheetName);
        temp.ppcopy(temp.make_and_share_and_rip_info());
        return temp;