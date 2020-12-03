# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 10:44:06 2020

@author: david
"""
from Patent2Net.P2N_Lib import LoadBiblioFile
from Patent2Net.P2N_Config import LoadConfig
import os, pickle

configFile = LoadConfig()
requete = configFile.requete
projectName = configFile.ndf
Gather = configFile.GatherContent
GatherBiblio = configFile.GatherBiblio
GatherPatent = configFile.GatherPatent
GatherFamilly = configFile.GatherFamilly
ResultPath = configFile.ResultBiblioPath
ndf = configFile.ndf


print("loading data file ", ndf+' from ', ResultPath, " directory.")
if 'Description'+ndf in os.listdir(ResultPath): # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
    data1 = LoadBiblioFile(ResultPath, ndf)


ResultPath = ResultPath.replace('DATA/', 'DATA/OLD/')

if 'Description'+ndf in os.listdir(ResultPath): # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
    try:
        data2 = LoadBiblioFile(ResultPath, ndf)
    except:
         with open(ResultPath + '//' + ndf, 'rb') as fic:
             data2 = dict()
             data2['brevets'] =[]
             Ok = True
             while Ok:
                 try:
                     data2['brevets'] .append(pickle.load(fic))
                 except EOFError:
                     Ok = False
                     pass


dataB1 =data1['brevets']

dataB2 =data2['brevets']

labB1 = [bre['label'] for bre in dataB1]

labB2 = [bre['label'] for bre in dataB2]

print(ndf, " variations ")
print ("brevets avant : ", len(labB2))

print ('Nouvelle taille :', len(labB1))
trucs = [lab for lab in labB2 if lab not in labB1]
print ("Les diparus :", trucs)
trucs2 = [lab for lab in labB1 if lab not in labB2]
print ("les nouveaux : ", trucs2)


