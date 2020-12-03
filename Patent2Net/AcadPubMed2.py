# -*- coding: utf-8 -*-
"""
Created on Mon Apr  10 11:26:06 2019

@author: dreymond
"""



import codecs
import os


from pymed import PubMed

from Patent2Net.P2N_Lib import LoadBiblioFile
from Patent2Net.P2N_Config import LoadConfig
from Patent2Net.P2N_Lib_Acad import  Nettoie, IPCCategorizer, IPCExtractPredictionBrevet,PubMedCheckNameAndGetAffiliation, OPSChercheAbstractBrevet, IsInFrance
import time
from fuzzywuzzy import fuzz
import pickle

# =============================================================================
# Paramétrage
# =============================================================================
# Pour IPCCat
SeuilScorePrediction = 600 # les IPC de la catégorisation par l'API dont 
# le score est > SeuilScorePrediction sont retenus. ¶00 c'est bien

# put your credential from epo client in this file...
# chargement clés de client, utilisé pour récupérer l'abstract du brevet du gugusse retrouvé


pubmed = PubMed(tool="P2N-Acad", email="patent2net@gmail.com")    
with open ('../PubMedKey.txt', 'r') as fic:
    pubApiKey = fic.read()
    pubApiKey = pubApiKey.strip()

PotentielAuteurs = list()


configFile = LoadConfig()

requete = configFile.requete
projectName = configFile.ndf

# La liste des structures adéquates s'appuie sur un fichier dans AcadRessources 
# encodé  en UTF8 avec une affiliation par ligne
#BonneAffiliation= LoadAffiliation('BonnesAffiliations.csv') #['laboratoire', 'institut', "centre de recherche", "université"] #à compléter
# Les champs nécessaires par brevet.
NeededInfo = ['label', 'date', 'inventor', 'title', 'abstract']
#Paramétrages pour sauvegarde des résultats : les répertoire sont fonction du fichier 
#requete.cql
ndf = projectName
BiblioPath = configFile.ResultBiblioPath
ResultBiblioPath = configFile.ResultBiblioPath
temporPath = configFile.temporPath
ResultPathContent= configFile.ResultContentsPath
ResultAbstractPath = configFile.ResultAbstractPath
Auteur = configFile.ResultPath + '//AcadCorpora'
RepDir = configFile.ResultPath + '//AcadCorpora'
ResultPath = configFile.ResultPath
project = RepDir
if 'AcadCorpora' not in os.listdir(configFile.ResultPath):
    os.makedirs(RepDir)
#Version simple... on ne prends pas les familles
if 'Description'+ndf in os.listdir(BiblioPath): # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
    print( "loading patent biblio data with ", " and ".join(NeededInfo), " fields.")
    DataBrevet = LoadBiblioFile(BiblioPath, ndf)
    print("Hi this is PubMeD processor. Bibliographic data of ", ndf, " patent universe found.")
else: #Retrocompatibility #Je me demande si c'est utile depuis la V3 ???
    print("please use Comptatibilizer")
#    for ndf in [fic2 for fic2 in os.listdir(ResultBiblioPath) if fic2.count('Description')==0]:
#        if ndf.startswith('Families'):
#            typeSrc = 'Families'
#        else:
#            typeSrc = ''
#        if ('Description'+ndf in os.listdir(ResultBiblioPath)) or ('Description'+ndf.lower() in os.listdir(ResultBiblioPath)): # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
#            ficBrevet = LoadBiblioFile(ResultBiblioPath, ndf)

typeSrc = ''
print("Nice, ", len(DataBrevet["brevets"]), " patents found. On cherche les auteurs...")
NbAut = 0 # Auteurs brevets testés

NumAut = 0 #Numero d'auteur pour les homonymes



# sauvegarde résultats
if 'traceAuct.csv' not in os.listdir(RepDir + "//"):
    with open(RepDir + "//" +'traceAuct.csv', "a", encoding='utf8') as  SavTrace:
        Entete = "Nom Inventeur ; Nombre publications ; Nombre publication matchées; AffilFr \n"
        SavTrace.write(Entete)
    # try: = []
try:
    with open(RepDir+"//traceAuct.csv", "r") as ficVus:
        AutDejaVus = ficVus.readlines()
    AutDejaVus = [lab.split(';')[0] for lab in AutDejaVus[1:]]
except:
    AutDejaVus = [] # Les noms d'inventeurs déjà traités                    

Inventeurs = []
DejaVus = []
Prod = dict()
for bre in DataBrevet['brevets']:
    Nom = Nettoie(bre['inventor'])
    if isinstance (Nom, list) and len(Nom) >0: 
        Nom = [ noms.title() for noms in Nom]
    elif isinstance (Nom, str) and len(Nom) >0:
        Nom = Nom.title()
    else:
        continue
    Inventeurs.extend(Nom)
    for nom in Nom:
        if nom in Prod.keys():
            Prod[nom].append(bre)
        else:
            Prod[nom] = [bre]
            
print("nb inventeurs déjà traités", len(AutDejaVus))                    
print ("sur ", len(Prod.keys()))            
print ("Resteraient ", len ([aut for aut in Prod.keys() if aut not in AutDejaVus]))   

InvDejaVus =[]
Inventeur_Norm = dict()
Inventeurs = set(Inventeurs)
try:
    with open(ResultPath+"/IndejaVus.pkl", 'r') as ficInv:    
        Prod = pickle.loads(Prod)
        InvDejaVus = Prod.keys()
except:
    pass
for inv in Inventeurs:
  if inv.title() not in InvDejaVus:
        reste = Inventeurs- set([inv]+InvDejaVus)
        InvDejaVus.append(inv)
        for inv2 in reste:
            if fuzz.token_sort_ratio(inv, inv2)>89:
                if len(inv) == len(inv2) and inv.split()[0] != inv2.split()[1] and '-' not in inv and '-' not in inv2:
                    print ("Suspects : ", inv, inv2)
                InvDejaVus.append(inv2)
                if inv in Inventeur_Norm.keys():
                    Inventeur_Norm [inv].append(inv2)  
                    for bre in Prod[inv2]:
                         Prod[inv].append(bre)
                    Prod.pop(inv2) # delete bad case
                else:
                    Inventeur_Norm [inv] = [inv2]
                    for bre in Prod[inv2]:
                         Prod[inv].append(bre)
                    Prod.pop(inv2) # delete bad case
    
with open(ResultPath+"/IndejaVus.pkl", 'w') as ficInv:    
    pickle.dumps(Prod)
    

AffilAuteur = dict()
for nomInv in Prod.keys():
    #ligne = Auteur + ";" + str(NbFr) + ";" +str(match) + ";" + AffiFr+"\n"
    if nomInv in Inventeur_Norm:
        if nomInv not in Inventeur_Norm.keys():
            tempo = [cle for cle in Inventeur_Norm.keys() if nomInv in Inventeur_Norm [cle]]
            nomInv = tempo [0]
            if nomInv not in Prod.keys():
                # hceck consistency
                print ("ARGGGGG")
    if nomInv not in AutDejaVus:
        query = "%s[Author - Full]" %(nomInv)
        Auteur = nomInv
        AutDejaVus.append(nomInv)
        DocsAuteur = pubmed.query(query, max_results=500)
        IramFull = """"""# le contenu du fichier IRAMUTEQ complet
        Num = 0 #le numéro de doc pour sauvegarde
        auteurDejaVu = False
        NbArt = 0 # Articles retrouvés
        NbFr  = 0 # articles avec afill Fr de l'auteur
        match =  0 # Le nombre de match brevet / article pour l'auteur
        AffiFr = False
        time.sleep(3.1)
        for article in DocsAuteur:
            NbArt +=1 
            SAV = False  # switch pour savegarder dans le csv
        #    print(type(article))
        #    print(article.toJSON())

            time.sleep(3.1)
            Num +=1
            try:
                Affi = PubMedCheckNameAndGetAffiliation(article.pubmed_id.split('\n')[0], Auteur, apikey=pubApiKey) # the first pubmed_id is the article. Others are citations
            except:
                time.sleep(30)
                Affi = PubMedCheckNameAndGetAffiliation(article.pubmed_id.split('\n')[0], Auteur, apikey=pubApiKey) # the first pubmed_id is the article. Others are citations

            if Affi is not None:
                if Auteur not in AffilAuteur.keys():
                    AffilAuteur[Auteur] = set()
                    AffilAuteur[Auteur].add(Affi)
                    if IsInFrance(Affi):
                        AffiFr = True
                    else:
                        AffiFr = False
                else:
                    if IsInFrance(Affi):
                        AffiFr = True
                    else:
                        AffiFr = False
                    AffilAuteur[Auteur].add(Affi)
                
                if AffiFr: #" france" in Affi.lower():  # very bad. Should check adress with geonames 
                    NbFr +=1
                    RepStockage = RepDir + "/Fr/" +str(NumAut) +'-'+ Auteur.title().replace(' ', '').replace('"', '') 
                else:
                    RepStockage = RepDir + "/NoFr/" +str(NumAut) +'-'+ Auteur.title().replace(' ', '').replace('"', '') 
                if "AcadCorpora" not in os.listdir(ResultPath):
                    os.makedirs(RepDir)
                    os.makedirs(RepDir + "/NoFr/")
                    os.makedirs(RepDir + "/Fr/")
                elif "NoFr" not in os.listdir(RepDir):
                    os.makedirs(RepDir + "/NoFr/")
                elif "Fr" not in os.listdir(RepDir):
                    os.makedirs(RepDir + "/Fr/")
                else:
                    pass
                if Auteur.title().replace(' ', '').replace('"','') +str(NumAut) not in os.listdir(RepDir):
                            try:
                                os.makedirs(RepStockage+"//publis")
                                os.makedirs(RepStockage+"//abstracts")
                            except:
                                pass
                else:
                        pass
                if  Auteur.title().replace(' ', '').replace('"', '') + 'Match.csv' not in os.listdir(RepStockage):
                        with codecs.open(RepStockage+ '//' + Auteur.title().replace(' ', '').replace('"', '') + 'Match.csv', 'w', 'utf8') as fic:
                            fic.write('Label Brevet;Résume brevet;CIBs associées;année;Article Pubmed_id;Article DOI;Article résumé;CIBs associées;CIB Match;score Max IPCCat;Année;Affiliation\n')
                    
                    #if not SavBrevet: #sauvegarde de l'abstract brevet
                for brevet in Prod [Auteur]:
                        AbsBrevet = OPSChercheAbstractBrevet(brevet, RepStockage+'//')
                        SavBrevet = True
                        EnTete = "**** *inventeur_" + Auteur.title().replace(' ', '') + " *date_"+ str(brevet['year']) + ' *brevet_'+brevet['label'] + ' *article_brevet \n'
                        ContPat  = brevet['title'] + '\n'
                        if 'fr' in AbsBrevet.keys():
                            ContPat  += '\n'.join(AbsBrevet ['fr'])
                            IPCBrevet = IPCCategorizer(ContPat , 'fr')
                            IPCBrevet= IPCExtractPredictionBrevet(IPCBrevet, SeuilScorePrediction)
                            
                            ResumeBrevet = '\n'.join (AbsBrevet ['fr'])
                        else:
                            ResumeBrevet =''
                            for lang in AbsBrevet.keys():
                                score = 0
                                if lang in ['en', 'fr', 'es', 'de', 'ru']:
                                    ContPat  += '\n'.join(AbsBrevet [lang]) 
                                    IPCBrevetTemp = IPCCategorizer(ContPat, lang)
                                    IPCBrevet= IPCExtractPredictionBrevet(IPCBrevetTemp, SeuilScorePrediction)
                                    
                                    ResumeBrevet += '\n'.join (AbsBrevet [lang])

                                                              
                                #Contenu += '\n'.join (AbsBrevet [lang])
                        IramFull += EnTete + ResumeBrevet  +'\n'
                        if isinstance(brevet['year'], list):
                            date = brevet['year'][0]
                        else:
                            date = str(brevet['year'])
                        ndf = date + '-'+brevet['label']+'.txt'
                        with codecs.open(RepStockage+ '//abstracts//' + ndf, 'w', 'utf8') as fic:
                            fic.write(EnTete + ContPat+'\n')
                        #On rajoute l'article
                        if article.abstract and article.title:
                            if not article.publication_date:
                                date = 1900
                            else:
                                date = article.publication_date.year
                            EnTete = "**** *inventeur_" + Auteur.title().replace(' ', '') + " *date_"+ str(date) + ' *brevet_article' + ' *article_'+article.pubmed_id.split('\n')[0]+ ' \n'

                            Contenu = article.title + '\n' + article.abstract + '\n'
                            IramFull += EnTete + Contenu
                            ndf = str(date) + '-' + str(Num) + '.txt'
    #                               # On stocke chaque résumé dans un fichier dans le rep abstract
                            with codecs.open(RepStockage+ '//publis//' + ndf, 'w', 'utf8') as fic:
                                fic.write(EnTete + Contenu+'\n')
                            
                            IPC = IPCCategorizer(Contenu, 'en') # on suppose tous les aarticles en anglais
                            IPCArt = IPCExtractPredictionBrevet(IPC, SeuilScorePrediction)
                            if IPCArt:
                                score = max([int(cat['score']) for cat in IPCArt])
                                
    #                        for cat in IPCArt:
    #                            for cat2 in IPCBrevet:
    #                                if cat['category'] == cat2 ["category"]:
    #                                    print ("Match found")
    #                                    SAV = True
                                CatIPCArt = set([cat['category'][0:7] for cat in IPCArt])
                                try:#on essaye le classement par IPCCat (pour ne pas avoir à éventuellement traiter les diff de schéma)
                                    CatIPCBrevet = set([cat['category'][0:7] for cat in IPCBrevet])
                                    
                                except: #le classement s'est mal passé on prend celui du brevet
                                    IPCBrevet = [{'category' : cib} for cib in brevet['IPCR7']]
                                    CatIPCBrevet = set([cat['category'][0:7] for cat in IPCBrevet])
                                MatchCat = [cat for cat in CatIPCArt if cat in CatIPCBrevet]
                            else:
                                MatchCat =''
                                IPCArt = {'category':''}
                            if len(MatchCat) >0:
                                print ("Match found")
                                SAV = True
                        else:
                            pass #titre ou contenu manquant

                                    
                if SAV:
                    if MatchCat is None:
                        MatchCat = []
                    else:
                        match +=1
                    if not article.publication_date:
                            dateArticle = str(1900)
                    else:
                            dateArticle = str(article.publication_date.year)
                    
                    if not article.doi:
                        article.doi = ''
                    try:
                        temp =  brevet['label'] +';'+ ResumeBrevet.replace(';', '*%*').replace('\n', '') + ';' +\
                                      ','.join([cat["category"] for cat in IPCBrevet]) +';' +\
                                     str(','.join(brevet['year']))+';' +article.pubmed_id.split('\n')[0] +';'+\
                                     article.doi +';' + Contenu.replace(';', '*%*').replace('\n', '') + ';' +\
                                     ','.join([cat["category"] for cat in IPCArt]) +";" +\
                                      ','.join([truc for truc in MatchCat]) + ";" + str(score) +';' + dateArticle +';' + Affi.replace('\n', '') + '\n'
                        with codecs.open(RepStockage+ '//' + Auteur.title().replace(' ', '').replace('"', '') + 'Match.csv', 'a', 'utf8') as fic:
                              fic.write(temp)  
                    except:
                        pass # strange pass
                          
                else:
                        if not auteurDejaVu:
                            auteurDejaVu = True
                            with open(RepDir + "//" "AffiliationsPasOk.csv", "a", encoding='utf8') as  SavAffil:
                                SavAffil.write(Auteur +';' + Affi.replace(';', '***') + '\n')
                                
                        pass #Not a frenchy
    #                    print ("pas glop", Affi)

    # =============================================================================
    #                 if not auteurDejaVu:
    #                     auteurDejaVu = True
    #                     with open(RepDir + "//" "AuteursTestes.csv", "a") as  SavAut:
    #                         SavAut.write(Auteur +';' + Affi.replace(';', '***') + '\n')
    # 
    # =============================================================================
                    #probablement un nom et prénom de correspondent pas
                    #ou l'affiliation n'a pas été reconnue
                    

            if Auteur in AffilAuteur.keys():
                with open(RepDir + "//" + "AuteursAffil.csv", "a", encoding='utf8') as  SavAutAffil:
                    temp = Auteur + ';' +";".join(AffilAuteur[Auteur]) + '\n'
                    if not Affi:
                        Affi='???'
                    SavAutAffil.write(Auteur +';' + Affi.replace(';', '***').replace('\n', '') + '\n')   
            if len(IramFull) >0:
                with codecs.open(RepStockage+ '//' + Auteur.title().replace(' ', '').replace('"', '') + 'IRAM.txt', 'w', 'utf8') as fic:
                    fic.write(IramFull)
    
   # print("estimations Auteurs brevets testés --> ", NbAut)
    # print("Articles retrouvés -->", NbArt)# 
    # print('Match ings articles / brevets', match)
    # print("les pampollos Français -->", NbFr) # 
        with open(RepDir + "//" +'traceAuct.csv', "a", encoding='utf8') as  SavTrace:
            # = Nom auteur ; Nb articles en Afill Fr ; nb articles matchés ; la dern affiliation
            ligne = Auteur + ";" + str(NbFr) + ";" +str(match) + ";" + str(AffiFr)+"\n"
            SavTrace.write(ligne)
                # try:
        #     if brevet['label'] not in DejaVus:
        #         with open(RepDir+"//DejaTraites.csv", "a", encoding='utf8') as ficVus:
        #             ficVus.write(brevet['label'] + '\n')
        # except:
        #     with open(RepDir+"//DejaTraites.csv", "a", encoding='utf8') as ficVus:
        #         ficVus.write(brevet['label'] + '\n')
        # DejaVus.append(brevet['label'])
    # else:
    #     for Auteur in brevet['inventor'] :
    #         NbAut +=1
    #         NumAut +=1 


# for brevet in DataBrevet["brevets"]:
    
#     AffilAuteur = dict()


#     if brevet['label'] not in DejaVus:
        
#         for Auteur in brevet['inventor'] :
#             SavBrevet = False # Commutateur pour éviter de requêter 15 fois pour un brevet
#             LigneCsv = """""" # the csv file for mathching articles and patent at CIB level
#             NbAut +=1
#             Auteur = Auteur.title()
#             NumAut +=1 
#             query = "%s[Author - Full]" %(Auteur)
#             DocsAuteur = pubmed.query(query, max_results=500)
#             IramFull = """"""# le contenu du fichier IRAMUTEQ complet
#             Num = 0 #le numéro de doc pour sauvegarde
#             auteurDejaVu = False
#             NbArt = 0 # Articles retrouvés
            
#             for article in DocsAuteur:
#                 NbArt +=1 
#                 SAV = False  # switch pour savegarder dans le csv
#             #    print(type(article))
#             #    print(article.toJSON())
#                 Num +=1
#                 Affi = PubMedCheckNameAndGetAffiliation(article.pubmed_id.split('\n')[0], Auteur) # the first pubmed_id is the article. Others are citations
#                 if Affi is not None:
#                     if Auteur not in AffilAuteur.keys():
#                         AffilAuteur[Auteur] = set()
#                         AffilAuteur[Auteur].add(Affi)
#                     else:
#                         AffilAuteur[Auteur].add(Affi)
#                     if " france" in Affi.lower():  # very bad. Should check adress with geonames 
#                         NbFr +=1
#                         RepStockage = RepDir + "//" +str(NumAut) +'-'+ Auteur.title().replace(' ', '').replace('"', '') 
#                         if "AcadCorpora" not in os.listdir(configFile.ResultPath):
#                             os.makedirs(RepDir)
#                         else:
#                             pass
#                         if Auteur.title().replace(' ', '').replace('"','') +str(NumAut) not in os.listdir(RepDir):
#                                 try:
#                                     os.makedirs(RepStockage+"//publis")
#                                     os.makedirs(RepStockage+"//abstracts")
#                                 except:
#                                     pass
#                         else:
#                             pass
#                         if  Auteur.title().replace(' ', '').replace('"', '') + 'Match.csv' not in os.listdir(RepStockage):
#                             with codecs.open(RepStockage+ '//' + Auteur.title().replace(' ', '').replace('"', '') + 'Match.csv', 'w', 'utf8') as fic:
#                                 fic.write('Label Brevet;Résume brevet;CIBs associées;année;Article Pubmed_id;Article DOI;Article résumé;CIBs associées;CIB Match;score Max IPCCat;Année;Affiliation\n')
                        
#                         if not SavBrevet: #sauvegarde de l'abstract brevet
#                             AbsBrevet = OPSChercheAbstractBrevet(brevet, RepStockage+'//')
#                             SavBrevet = True
#                             EnTete = "**** *inventeur_" + Auteur.title().replace(' ', '') + " *date_"+ str(brevet['year']) + ' *brevet_'+brevet['label'] + ' *article_brevet \n'
#                             ContPat  = brevet['title'] + '\n'
#                             if 'fr' in AbsBrevet.keys():
#                                 ContPat  += '\n'.join(AbsBrevet ['fr'])
#                                 IPCBrevet = IPCCategorizer(ContPat , 'fr')
#                                 IPCBrevet= IPCExtractPredictionBrevet(IPCBrevet, SeuilScorePrediction)
                                
#                                 ResumeBrevet = '\n'.join (AbsBrevet ['fr'])
#                             else:
#                                 ResumeBrevet =''
#                                 for lang in AbsBrevet.keys():
#                                     score = 0
#                                     if lang in ['en', 'fr', 'es', 'de', 'ru']:
#                                         ContPat  += '\n'.join(AbsBrevet [lang]) 
#                                         IPCBrevetTemp = IPCCategorizer(ContPat, lang)
#                                         IPCBrevet= IPCExtractPredictionBrevet(IPCBrevetTemp, SeuilScorePrediction)
                                        
#                                         ResumeBrevet += '\n'.join (AbsBrevet [lang])

                                                                  
#                                     #Contenu += '\n'.join (AbsBrevet [lang])
#                             IramFull += EnTete + ResumeBrevet  +'\n'
#                             if isinstance(brevet['year'], list):
#                                 date = brevet['year'][0]
#                             else:
#                                 date = str(brevet['year'])
#                             ndf = date + '-'+brevet['label']+'.txt'
#                             with codecs.open(RepStockage+ '//abstracts//' + ndf, 'w', 'utf8') as fic:
#                                 fic.write(EnTete + ContPat+'\n')
#                             #On rajoute l'article
#                             if article.abstract and article.title:
#                                 if not article.publication_date:
#                                     date = 1900
#                                 else:
#                                     date = article.publication_date.year
#                                 EnTete = "**** *inventeur_" + Auteur.title().replace(' ', '') + " *date_"+ str(date) + ' *brevet_article' + ' *article_'+article.pubmed_id.split('\n')[0]+ ' \n'

#                                 Contenu = article.title + '\n' + article.abstract + '\n'
#                                 IramFull += EnTete + Contenu
#                                 ndf = str(date) + '-' + str(Num) + '.txt'
#         #                               # On stocke chaque résumé dans un fichier dans le rep abstract
#                                 with codecs.open(RepStockage+ '//publis//' + ndf, 'w', 'utf8') as fic:
#                                     fic.write(EnTete + Contenu+'\n')
                                
#                                 IPC = IPCCategorizer(Contenu, 'en') # on suppose tous les aarticles en anglais
#                                 IPCArt = IPCExtractPredictionBrevet(IPC, SeuilScorePrediction)
#                                 if IPCArt:
#                                     score = max([int(cat['score']) for cat in IPCArt])
                                
#         #                        for cat in IPCArt:
#         #                            for cat2 in IPCBrevet:
#         #                                if cat['category'] == cat2 ["category"]:
#         #                                    print ("Match found")
#         #                                    SAV = True
#                                     CatIPCArt = set([cat['category'][0:7] for cat in IPCArt])
#                                     try:#on essaye le classement par IPCCat (pour ne pas avoir à éventuellement traiter les diff de schéma)
#                                         CatIPCBrevet = set([cat['category'][0:7] for cat in IPCBrevet])
                                        
#                                     except: #le classement s'est mal passé on prend celui du brevet
#                                         IPCBrevet = [{'category' : cib} for cib in brevet['IPCR7']]
#                                         CatIPCBrevet = set([cat['category'][0:7] for cat in IPCBrevet])
#                                     MatchCat = [cat for cat in CatIPCArt if cat in CatIPCBrevet]
#                                 else:
#                                     MatchCat =''
#                                 if len(MatchCat) >0:
#                                     print ("Match found")
#                                     SAV = True
#                             else:
#                                 pass #titre ou contenu manquant
#                         else: # Le brevet a déjà été retrouvé
#                             if article.abstract and article.title:
#                                 if not article.publication_date:
#                                     date = 1900
#                                 else:
#                                     date = article.publication_date.year

#                                 EnTete = "**** *inventeur_" + Auteur.title().replace(' ', '') + " *date_"+ str(date)  + ' *brevet_article' +'\n'
                                
#                                 Contenu = article.title + '\n' + article.abstract + '\n'
#                                 IramFull += EnTete + Contenu+'\n'
#                                 ndf = str(date) + '-' + str(Num) + '.txt'
#         #                               # On stocke chaque résumé dans un fichier dans le rep abstract
#                                 with codecs.open(RepStockage+ '//publis//' + ndf, 'w', 'utf8') as fic:
#                                     fic.write(EnTete + Contenu+'\n')
#                                 IPC = IPCCategorizer(Contenu, 'en')# on suppose tous les aarticles en anglais
#                                 IPCArt = IPCExtractPredictionBrevet(IPC, SeuilScorePrediction)
#                                 if IPCArt:
#                                     CatIPCArt = set([cat['category'][0:7] for cat in IPCArt])
#                                     if IPCBrevet:
#                                         CatIPCBrevet  = set([cat['category'][0:7] for cat in IPCBrevet])
#                                     elif brevet ['IPCR7']:
#                                         CatIPCBrevet = set(brevet ['IPCR7'])
#                                     else:
#                                         break
#                                     MatchCat = [cat for cat in CatIPCArt if cat in CatIPCBrevet]
#                                     score = max([int(cat['score']) for cat in IPCArt])
#                                     if len(MatchCat) >0:
#                                         print ("Match found")
#                                         SAV = True
#                                 else:
#                                     print( IPCArt )
#                                     pass
#                             else:
#                                 pass
                                        
#                         if SAV:
#                             match +=1
#                             if not article.publication_date:
#                                     dateArticle = str(1900)
#                             else:
#                                     dateArticle = str(article.publication_date.year)
                            
#                             if not article.doi:
#                                 article.doi = ''
                            
#                             temp =  brevet['label'] +';'+ ResumeBrevet.replace(';', '*%*').replace('\n', '') + ';' +\
#                                           ','.join([cat["category"] for cat in IPCBrevet]) +';' +\
#                                          str(','.join(brevet['year']))+';' +article.pubmed_id.split('\n')[0] +';'+\
#                                          article.doi +';' + Contenu.replace(';', '*%*').replace('\n', '') + ';' +\
#                                          ','.join([cat["category"] for cat in IPCArt]) +";" +\
#                                           ','.join([truc for truc in MatchCat]) + ";" + str(score) +';' + dateArticle +';' + Affi.replace('\n', '') + '\n'
#                             with codecs.open(RepStockage+ '//' + Auteur.title().replace(' ', '').replace('"', '') + 'Match.csv', 'a', 'utf8') as fic:
#                                   fic.write(temp)  
                            
                          
#                     else:
#     #                    if not auteurDejaVu:
#     #                        auteurDejaVu = True
#     #                        with open(RepDir + "//" "AffiliationsPasOk.csv", "a") as  SavAffil:
#     #                            SavAffil.write(Auteur +';' + Affi.replace(';', '***') + '\n')
#     #                            
#                         pass #Not a frenchy
#     #                    print ("pas glop", Affi)
#                 else:
#     # =============================================================================
#     #                 if not auteurDejaVu:
#     #                     auteurDejaVu = True
#     #                     with open(RepDir + "//" "AuteursTestes.csv", "a") as  SavAut:
#     #                         SavAut.write(Auteur +';' + Affi.replace(';', '***') + '\n')
#     # 
#     # =============================================================================
#                     #probablement un nom et prénom de correspondent pas
#                     #ou l'affiliation n'a pas été reconnue
                    
#                     pass
#             if Auteur in AffilAuteur.keys():
#                 with open(RepDir + "//" "AuteursAffil.csv", "a", encoding='utf8') as  SavAutAffil:
#                     temp = Auteur + ';' +";".join(AffilAuteur[Auteur]) + '\n'
#                     if not Affi:
#                         Affi='???'
#                     SavAutAffil.write(Auteur +';' + Affi.replace(';', '***').replace('\n', '') + '\n')   
#             if len(IramFull) >0:
#                 with codecs.open(RepStockage+ '//' + Auteur.title().replace(' ', '').replace('"', '') + 'IRAM.txt', 'w', 'utf8') as fic:
#                     fic.write(IramFull)
#         try:
#             if brevet['label'] not in DejaVus:
#                 with open(RepDir+"//DejaTraites.csv", "a", encoding='utf8') as ficVus:
#                     ficVus.write(brevet['label'] + '\n')
#         except:
#             with open(RepDir+"//DejaTraites.csv", "a", encoding='utf8') as ficVus:
#                 ficVus.write(brevet['label'] + '\n')
#         DejaVus.append(brevet['label'])
#     else:
#         for Auteur in brevet['inventor'] :
#             NbAut +=1
#             NumAut +=1 
            


#        ScoreAuteur = 0
#        ListePaysAffiliation = list()  #Les pays de l'affiliation des documents
#                  for document in DocsAuteur['docs']:
#                        if isinstance(document, dict):
#                            if 'abstract_s' in document.keys(): #pas toutes les entréees HAL ont un abstract
#                                Num +=1
#                                if  'producedDate_s' in document.keys():
#                                    Date = document['producedDate_s']
#                                else:
#                                    Date = 1000
#                                if 'title_s' in document.keys():
#                                    Titre =  document['title_s']
#                                else:
#                                    Titre = "Pas de titre"
#                                Entete= "**** *auteur_" + Auteur.title().replace(" ", "").replace('"','') + " *date_"+ str(Date) + '\n'
#                                Contenu =  '\n'.join(document['abstract_s'])
#                                ndf = str(Date) + '-' + str(Num) + '.txt'
#                                # On stocke chaque résumé dans un fichier dans le rep abstract
#                                with codecs.open(RepStockage+ '\\abstracts\\' + ndf, 'w', 'utf8') as fic:
#                                    fic.write(Entete + Contenu)
#                                IramFull += Entete + Contenu + "\n"
#                                
#                    #Pour chaque auteur la somme des titres résumé dans le format Iramuteq
#                    with codecs.open(RepStockage+'\\IRAM' +Auteur.title().replace(' ', '').replace('"','') +str(NumAut)+'.txt', 'w', 'utf8') as fic:
#                        fic.write(IramFull)
#                        
#                    #la suite est adaptée du script de récup des résumés 
#                    #si on a trouvé un match dans scolar, on récupère l'abstract
                        
                                                    
                        #OPS limitation ?
                        #OPS includes character-coded full text only for EP, WO, AT, CH, CA, GB and ES.
                        #http://forums.epo.org/open-patent-services-and-publication-server-web-service/topic3728.html



#                    if data is not None and data.ok:
#                        contenu = content.replace(typeSrc, "")
#
#                        patentCont = data.json()
#                        Langs = MakeIram2(brevet, ndb +'.txt', patentCont, RepDir+ '//'+ typeSrc + contenu+'//', contenu)

#        NumAut = 0 # Numero d'auteurs
#        if len(GoodPotentielAuteur)>0:
#            for auteur in GoodPotentielAuteur:
#                IramFull ="""""" #the complete IramuTeq File
#                NumAut+=1
#                Publis = []
#                # la librairie a seulement téléchargé titre et année dans les ref biblio
#                # on complète
#                for publi in auteur.publications:
#                    Publis.append(publi.fill())
#                    
#                DocsAuteur['docs'][1]['submittedDate_s']
#                if "AcadCorpora" not in os.listdir(configFile.ResultPath):
#                    os.makedirs(RepDir)
#                if Auteur.title().replace(' ', '') +str(NumAut) not in os.listdir(RepDir):
#                    os.makedirs(RepStockage+"\\publis")
#                    os.makedirs(RepStockage+"\\abstracts")
#                Num = 0 # Numero de Publis retrouvées
#                # récupération des publications
#                for pub in Publis:
#                    Num+=1
#                    if 'year' not in pub.bib.keys():
#                        pub.bib['year'] = 1000
#                    if 'title' not in pub.bib.keys():    
#                        pub.bib['title'] = "Titre inconnu"
#                    if 'eprint' in pub.bib.keys():
#                        try:
#                            req = requests.get(pub.bib['eprint'], allow_redirects=True)
#                            #recupération de l'extension de la ressource
#                            pathURl = urlparse(pub.bib['eprint'])
#                            extension = os.path.splitext(pathURl.path)[1]
#                            if extension is None or extension =='': #on force le pdf
#                                extension='.pdf'
#                            # création du nom de la ressource
#                            ndf = pub.bib['title'].title().replace(' ', '')+ '-' + str(pub.bib['year']) + '-' + str(Num) + extension 
#                            with open(RepStockage+ '\\publis\\' + ndf, 'wb') as fic:
#                                fic.write(req.content)
#                        except:
#                            pass
#                    elif 'url' in pub.bib.keys():
#                        #use unpayload here...
#                        pass
#                    else:
#                        pass
#                    if 'abstract' in pub.bib.keys():
#                        #formatage IRAMUTEQ
#                        Entete= "**** *auteur_" + Auteur.replace(" ", "") + " *date_"+ str(pub.bib['year']) + '\n'
#                        Contenu = pub.bib['title'] + '\n' +  pub.bib['abstract'].text
#                        ndf = str(pub.bib['year']) + '-' + str(Num) + '.txt'
#                        # On stocke chaque résumé dans un fichier dans le rep abstract
#                        with codecs.open(RepStockage+ '\\abstracts\\' + ndf, 'w', 'utf8') as fic:
#                            fic.write(Entete + Contenu)
#                        IramFull += Entete + Contenu + "\n"
#                        #Pour chaque auteur la somme des titres résumé dans le format Iramuteq
#                with codecs.open(RepStockage+'\\IRAM' +Auteur.title().replace(' ', '') +str(NumAut)+'.txt', 'w', 'utf8') as fic:
#                    fic.write(IramFull)
#                    
 