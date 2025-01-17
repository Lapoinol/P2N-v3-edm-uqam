# -*- coding: utf-8 -*-
"""
Created on Sun Feb 15 09:12:25 2015

@author: dreymond
"""

import datetime
import os

from Patent2Net.P2N_Config import LoadConfig
from Patent2Net.P2N_Lib import LoadBiblioFile, RenderTemplate
from Patent2Net.app.dex import set_done

nbFam = 0

configFile = LoadConfig()
requete = configFile.requete
ndf = configFile.ndf
Gather = configFile.GatherContent
GatherBiblio = configFile.GatherBiblio
GatherPatent = configFile.GatherPatent
GatherFamilly = configFile.GatherFamilly

# should set a working dir one upon a time... done it is temporPath
ResultBiblioPath = configFile.ResultBiblioPath
ResultPatentPath = configFile.ResultListPath
ResultContentsPath = configFile.ResultContentsPath

GlobalPath = configFile.GlobalPath

# take request from BiblioPatent file


# NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
if 'Description' + ndf in os.listdir(ResultBiblioPath):
    data = LoadBiblioFile(ResultBiblioPath, ndf)
    requete = data['requete']
else:  # Retrocompatibility
    print("please use Comptatibilizer")
    # if 'Fusion' in data.keys()
    data = dict()
if GatherFamilly:  # pdate needed for families
    # NEW 12/12/15 new gatherer append data to pickle file in order to consume less memory
    if 'DescriptionFamilies' + ndf in os.listdir(ResultBiblioPath):
        data2 = LoadBiblioFile(ResultBiblioPath, 'Families' + ndf)
        nbFam = len(data2['brevets'])
    else:  # Retrocompatibility
        print("No Families. please use gather them")
    # if 'Fusion' in data.keys()with open( ResultBiblioPath+'/Families'+ndf, 'r') as ficBib:
 #        data2 = cPickle.load(ficBib)

else:
    nbFam = 0


today = datetime.datetime.today()
date = today.strftime('%d, %b %Y')

totalPatents = ""
if "brevets" in data:  # compatibility, this may be useless
    totalPatents = len(data["brevets"])
else:
    totalPatents = "see datatable :-)"

# new method to count documents by type
totalsPerType = []
totalsPerFamilyType = []
if Gather:
    def generateTotal(content):
        path = os.path.join(ResultContentsPath, content).replace('\\','/')
        if os.path.isdir(path):
            lstfic = os.listdir(path)
            languages = set([str(fi[0:2]) for fi in lstfic])
            totalLanguages = {l: 0 for l in languages}
            for fi in lstfic:
                totalLanguages[str(fi[0:2])] += 1
            return {
                "type": content,
                "total": len(lstfic),
                "languages": totalLanguages
            }
        else:
            print('WARNING: Directory "{}" does not exist'.format(path))

        return {
            "type": content,
            "total": 0,
            "languages": {},
        }

    for content in ['Abstract', 'Claims', 'Description']:
        totalsPerType.append(generateTotal(content))

    for content in ['FamiliesAbstract', 'FamiliesClaims', 'FamiliesDescription']:
        totalsPerFamilyType.append(generateTotal(content))

outfile = GlobalPath + '/' + ndf + '.html'
print('Writing "{outfile}"'.format(outfile=outfile))

print(configFile.show())

RenderTemplate(
    "ModeleContenuIndex2.html",
    outfile,
    GlobalPath=GlobalPath,
    CollectName=ndf,
    Request=requete,
    TotalPatents=totalPatents,
    TotalFamily=nbFam,
    HasFamily=GatherFamilly,
    Date=date,
    TotalsPerType=totalsPerType,
    TotalsPerFamilyType=totalsPerFamilyType,

    InventorNetwork=configFile.InventorNetwork,
    ApplicantNetwork=configFile.ApplicantNetwork,
    ApplicantInventorNetwork=configFile.ApplicantInventorNetwork,
    InventorCrossTechNetwork=configFile.InventorCrossTechNetwork,
    ApplicantCrossTechNetwork=configFile.ApplicantCrossTechNetwork,
    CountryCrossTechNetwork=configFile.CountryCrossTechNetwork,
    CrossTechNetwork=configFile.CrossTechNetwork,
    CompleteNetwork=configFile.CompleteNetwork,
    References=configFile.References,
    Citations=configFile.Citations,
    Equivalents=configFile.Equivalents,

    FormateExportCountryCartography=configFile.FormateExportCountryCartography,
    FormateExportBiblio=configFile.FormateExportBiblio,
    FormateExportDataTable=configFile.FormateExportDataTable,
    FormateExportPivotTable=configFile.FormateExportPivotTable,

    FreePlane=configFile.FreePlane,
    FusionCarrot2=configFile.FusionCarrot2,
    Images=configFile.GatherImages,
	Cluster = configFile.Cluster
)


outfile = GlobalPath + '/' + ndf+'/'+ndf+'Carrot.html'
ModeleCarrot = "carrot2.html"
RenderTemplate(
    "carrot2.html",
    outfile,
    jsonFile='./PatentContents/Consistent/Carrot2_EN_Abstract_'+ndf+'.json',
    dataDir=ndf.replace('"', '').lower(),
    request = requete
)

set_done(ndf) # Done request with new dex systeme

print ('updating js file')
# updating index.js for server side and local menu
inFile = []  # memorize content
with open('../dex.js') as FicRes:
    data = FicRes.readlines()
    for lig in data[2:]:
        if '</ul>' not in lig and "');" not in lig:
            inFile.append(lig)
#print (inFile)
with open('../dex.js', 'w') as ficRes:
    ficRes.write("document.write('\ ".strip())
    ficRes.write("\n")
    ficRes.write(" <ul>\ ".strip())
    ficRes.write("\n")

    # write last analyse
    ficRes.write(
        """<li><a href="DATA/***request***.html" target="_blank">***request***</a></li>\ """.replace('***request***', ndf).strip())
    ficRes.write("\n")
    for exist in inFile:
        if ndf+'.html' not in exist:
            ficRes.write(exist.strip().replace('</ul>\ ', ''))
            ficRes.write("\n")
        else:
            pass
            #print(ndf)
    ficRes.write(" </ul>\ ".strip())
    ficRes.write("\n")
    ficRes.write("');")