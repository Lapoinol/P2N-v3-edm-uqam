# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 07:53:30 2014

@author: dreymond
"""
import codecs
import json
import os
from xml.sax.saxutils import escape

import bs4

from Patent2Net.P2N_Config import LoadConfig
from Patent2Net.P2N_Lib import LoadBiblioFile, AnnonceProgres

configFile = LoadConfig()
requete = configFile.requete
IsEnableScript = configFile.FusionCarrot2
GatherFamilly = configFile.GatherFamilly

def GenereListeFichiers(rep):
    """ prend un dossier en paramètre (chemin absolu) et génère la liste
    complète des fichiers TXT de l'arborescence"""
    listeFicFR = []
    listeFicEN = []
    listeFicUNK = []
    for root, subFolders, files in os.walk(rep):

        if len(subFolders)>0:
            for sousRep in subFolders:
                temporar = GenereListeFichiers(rep+'//'+sousRep)
                listeFicFR.extend(temporar[0])
                listeFicEN.extend(temporar[1])
                listeFicUNK.extend(temporar[2])
        else:
            for fichier in files:
                if fichier.endswith('.txt') and fichier.lower().startswith('fr'):
                    listeFicFR.append(root+'//'+fichier)
                elif fichier.endswith('.txt') and fichier.lower().startswith('en'):
                    listeFicEN.append(root+'//'+fichier)
                else:
                    if fichier.endswith('.txt'):
                        listeFicUNK.append(root+'//'+fichier)

    return (list(set(listeFicFR)), list(set(listeFicEN)), list(set(listeFicUNK)))

def Normalise(listeFic):
    """Necessary becaus in OPSGatentsPAtents, I didn't care about abstracts name,
    there is a missing '-' in name creation: should be LANG-PatentNum.txt"""
    cpt = 0
    for fic in listeFic:
        if fic.count('Abstracts')>0:
            tmp = fic.split('//')
            nomDeFic = tmp[len(tmp)-1]
            NouveauNom = nomDeFic[0:2].replace('-', '')  +'-'+ nomDeFic[2:].replace('-', '')

            try:
                os.rename(fic, fic.replace(nomDeFic, NouveauNom))
                cpt+=1
            except:
                pass
    print(cpt, " Abstracts files Names normalized")


def coupeEnMots(texte):
    "renvoie une liste de mots propres des signes de ponctuation et autres cochonneries"
    texte= texte.lower()
    import re
    res = re.sub('['+"[]?!"+']', ' ', texte) # on vire la ponctuation
    res = re.sub('\d', ' ', res) # extraction des chiffres #numeric are avoided
    res = re.findall('\w+', res, re.UNICODE) # extraction des lettres seulement #only letters, no symbols
    return res

def LectureFichier2(fic):
    """read the file, and return purged from coupeEnMots content if lenght is greater thar arbitrary value, here 5"""
    """cleans also Iramuteq Variables"""
    try:
        with codecs.open(fic, "r", 'utf8') as fichier:
    #            BAD 
    
                fi = fichier.readlines()
                #cpt = 0
    #            try:
    #                fi
    #                #tempo = bs.UnicodeDammit.detwingle(fi)
    #            except:
    #                fi = ""
    #                cpt +=1
    #                print "loupés ", cpt
    #
                meta = ''.join([lig for lig in fi if lig.startswith('****')])
                try:
                    for ligne in fi:
                        if not ligne.startswith('****'):
                            try:
                                pipo = ligne.encode('utf8')
                                pipo = pipo.decode('utf8')
                                lect = ''.join(ligne+'\n')
                            except:
                                lect=''
                                pass
    
                except:
                    lect=''
                if len(' '.join(coupeEnMots(lect)))> 5: #arbitrary
                    contenu =lect
                    return contenu, meta
                else:
                    return None, None
    except:
    # strange case as the file exists
        return None, None


def complete3(listeFic, lang, det, Brevets):

    resum = [fi for fi in set(listeFic) if fi.count('//'+det+'//')>0]
    dejaVu = []
    Ignore = 0
    dejaVu2 = []
     #as given in Carro2 input xml format
     #http://download.carrot2.org/head/3.11.0-SNAPSHOT/manual/#section.architecture.input-xml
    Contenu = """<?xml version="1.0" encoding='UTF-8'?>\n"""
    Contenu += "<searchresult>\n"
    Contenu += "<query>"+requete+"</query>\n"
    cmpt = 0
    dico = dict ()
    dico ["document"]= []
    for fichier in set(resum):
        dejaVu.append(fichier)
        
        tempo, meta =LectureFichier2(fichier)
        document = dict()
        if tempo is not None and meta is not None:
            try:
                Label = meta.split('Label_')[1].split(' ')[0].replace('.txt', '')
                Brev = [ele for ele in Brevets if ele['label'] == Label]
                if len(Brev) ==1:
                    if isinstance(Brev[0], dict):
                        try:
                            #titre = Brev[0]['title']
                            titre = bs4.BeautifulSoup(Brev[0]['title'], "lxml").text
                        except:
                            titre = Label
                        

                        url = "http://worldwide.espacenet.com/searchResults?compact=false&amp;ST=singleline&amp;query="+Label+"&amp;locale=en_EP&amp;DB=EPODOC"
                        cmpt += 1
                        try:
                            Content = bs4.BeautifulSoup(tempo, "lxml").text
                            #soupe =  bs4.BeautifulSoup(Content.prettify(Content))
                            tempo = Content#.encode('utf8')
                            # tempo=tempo.replace('&lt;', u'>')
                            # tempo=tempo.replace('&', '&amp;')
                            if tempo not in dejaVu2:
                                dejaVu2.append(tempo)
                                Contenu+='<document id="%s">\n' %cmpt
                                Contenu+='<title>%s</title>\n' % escape(titre)
                                Contenu+='<url>%s</url>\n' % url

                                Contenu+='<snippet>%s</snippet>\n' %escape(str(tempo))
                                Contenu+="</document>\n"
                                document ['content'] = escape(str(tempo))
                                document ['title'] = titre
                                document ['url'] = url
                                document ['language'] = lang
                            else:
                                Ignore+=1
                        except:
                            #print #bad encoding should be here
                            Ignore+=1
                    else:
                        pass # is this really bibliographic data ?

                else:
                    Ignore+=1
            except:
                Ignore+=1
                pass
            #cleaning temporarrary this should be done at gathering process
#            temp = tempo.split('\n')[1].strip()

        else:
            Ignore+=1
        if len(document)>0:
            dico ['document'].append (document)
    #print(len(set(resum)), "fichiers "+det+ " à traiter en langage : ", lang)
    #print(cmpt, " fichiers "+det+ " traités", end=' ')
    #if Ignore >0:
    #    print(" et ", Ignore, " fichier(s) ignores (non dédoublés)")
    Contenu += "</searchresult>"

    return Contenu.lower(), dico


if IsEnableScript:
    Rep = configFile.ResultContentsPath
    Bib = configFile.ResultBiblioPath
    Rep2 =  Rep + "/Consistent/EN"
    try:
        lstConsistents = os.listdir(Rep2)
    except: # fusion Iramuteq must be executed before or this is due to the patent set
        lstConsistents = []
    
    
    
    prefixes = [""]
    if GatherFamilly:
        prefixes.append("Families")

    for prefix in prefixes:
        ndf = prefix + configFile.ndf

        if 'Description'+ndf in os.listdir(Bib): # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
            DataBrevet = LoadBiblioFile(Bib, ndf)
            LstBrevet = DataBrevet['brevets']
        elif 'Description'+ndf.title() in os.listdir(Bib): # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
            DataBrevet = LoadBiblioFile(Bib, ndf.title())
            LstBrevet = DataBrevet['brevets']
        else: #Retrocompatibility
            print("please use Comptatibilizer")

        try:
            os.makedirs(Rep+"/Carrot2")
        except:
            #directory exists
            pass
        for bre in LstBrevet:
            if isinstance(bre['label'], list):
                bre['label'] = bre['label'] [0] # those patent with multiple labels GRRR
        temporar = GenereListeFichiers(Rep)
        cpt =0
        for det in ['Abstract', 'Claims', 'Description']:
            ind = 0
            cpt+=1
            for lang in ['FR', 'EN', 'UNK']:
                NomResult = lang+'_'+det.replace('Abstracts', '') + '_' + ndf+'.xml' # det.replace('Abstracts', '') this command is for old old mispelling :-(.. I think)
                ficRes = codecs.open(Rep+'//Carrot2//'+NomResult, "w", 'utf8')
                carrot2, jsondat = complete3(temporar[ind], lang, prefix+det, LstBrevet)
                ficRes.write(carrot2)
                ficRes.close()
                with codecs.open(Rep+'//Carrot2//'+NomResult.replace('.xml', '.json'), "w", 'utf8') as ficRes:
                    json.dump(jsondat, ficRes, indent = 4)
                    
                # lazy attempt for consistent vues
                #NomResult2 = lang+'_'+det.replace('Abstracts', '') + '_' + ndf+'.xml' # det.replace('Abstracts', '') this command is for old old mispelling :-(.. I think)
                ficRes2 = codecs.open(Rep+'/Consistent/Carrot2_'+NomResult, "w", 'utf8')
                ficRes2.write(carrot2)
                ficRes2.close()
                carrot2, json2 = complete3(temporar[ind], lang, prefix+det, [bre for bre in LstBrevet if 'EN-'+ bre ['label']+'.txt' in lstConsistents] )
                with codecs.open(Rep+'/Consistent/Carrot2_'+NomResult.replace('.xml', '.json'), "w", 'utf8') as ficRes:
                    json.dump( json2, ficRes, indent = 4)
                
                
                ind+=1
                AnnonceProgres (Appli = 'p2n_carrot', valMax = 100, valActu = 60+5*ind*cpt) #; say almost 10 loops (3x3 ^_^), 50% of progress bar should be missing here so I put 60... grosso modo

                ficRes.close()
        
