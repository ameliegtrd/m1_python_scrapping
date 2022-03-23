# -*- coding: utf-8 -*-

################################################################################
# fichier  : GOUTARD_Amelie_analyse.py
# Auteur : GOUTARD Amelie
################################################################################

''' 
Theme : Nature & Geography/Disasters/Extreme Weather 
Lien : https://www.thecanadianencyclopedia.ca/en/browse/things/nature-geography/disasters-extreme-weather?type=article
''' 

################################################################################
# Importation de fonctions externes :
import pandas as pd
import numpy as np
from numpy.linalg import norm
import pickle
import re
from math import *
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity

################################################################################
# Definition locale de fonctions :
def getTokens(doc):
    '''
    Renvoi un texte sous forme d'une liste de mots decoupes en minuscule et sans ponctuation 
    et sans nombres, inutile pour l'analyse du texte
    '''
    regex = r"""[a-zA-Z]+"""
    tokens = [word.strip().lower() for word in re.findall(regex, doc)]
    return tokens

################################################################################
# Definition de classes :

class DTM:
    def __init__(self, liste_tuple, mots_vides):
        # on recupere les titres et les urls
        les_url = []
        les_titres = []
        self.stopWords = mots_vides

        for tuple in liste_tuple :
            les_url.append(tuple[0])
            les_titres.append(tuple[1])

        self.url = les_url
        self.title = les_titres

        # construction du dataframe de mots

        termes_docs = []  # liste de dictionnaires, qui compte le nombre d'occurrences de chaque terme dans chaque doc
        for tuple in liste_tuple :
            texte = tuple[2]
            les_mots = getTokens(texte)
            dico = {} # dictionnaire qui va compter le nombre d'occurrences de chaque mot
            for mot in les_mots :
                if mot not in self.stopWords : # gestion des mots vides
                    dico[mot] = dico.get(mot,0)+1
            termes_docs.append(dico)
        self.data = pd.DataFrame(termes_docs).fillna(0)


        # Calcul du df : il faut connaitre le nombre de documents qui contiennent chaque terme
        df = self.data.astype('bool').sum()
        nbdoc = self.data.shape[0]
        log_idf = [log(nbdoc/value) for value in df]
        # print(self.data.max(axis=1))
        self.data = self.data.div(self.data.max(axis=1),axis=0)
        self.data = self.data.mul(log_idf,axis=1)
        # sur un dataframe, div et mul multiplient ou divisent sur toute la ligne (axis=0) ou sur la colonne (axis=1)

    def __repr__(self):
        return self.data.__repr__()

    def nBest(self,N):
        '''
        Renvoi les N termes les plus frequents dans le corpus entier avec leur frequence,
        par ordre decroissant
        '''
        return self.data.sum().sort_values(ascending=False)[:N]

    def nBestDoc(self,N,indice):
        '''
        Renvoi la liste des N termes les plus frequents d'un document avec leur frequence,
        par ordre decroissant
        '''
        return self.data.iloc[indice].sort_values(ascending=False)[:N]

    def query(self,requete):
        '''
        Renvoi la liste des documents contenant l'ensemble des mots de la requete
        '''
        mots_valides = [mot for mot in getTokens(requete) if mot not in self.stopWords]
        # s'il n'y a aucun mot valide (i.e que des mots outils), retourne une liste vide
        if len(mots_valides)==0:
            return []
        # si au moins un des mots de la requete n'est pas dans le dictionnaire de mot (i.e colonnes du dfm),
        # retourne une liste vide
        if not all (mot in self.data.columns for mot in mots_valides):
            return []
        # sinon, retourne la liste des urls (documents) qui contiennent tous les mots de la requete
        les_url = []
        for i in self.data.index:
            if all([self.data.loc[i,mot]>0 for mot in mots_valides]):
                les_url.append(self.url[i])
        return les_url
    
    def queryScore(self,chaine, N):
        '''
        Renvoi les urls des N documents les plus pertinents selon les scores tf-idf pour la chaine
        '''
        # liste des documents qui contiennent tous les mots de la requete
        l_urls = self.query(chaine)
        # on garde uniquement les colonnes du dfm qui contiennent tous les mots de la requete
        mots_valides = [mot for mot in getTokens(chaine) if mot not in self.stopWords]
        # gestion des exceptions
        if len(mots_valides)==0 :
            return []
        
        if not all (mot in self.data.columns for mot in mots_valides):
            return []
        
        else : 
            df = self.data[mots_valides]
            # ajout d'une colonne contenant la somme des scores par ligne
            sums = df.sum(axis=1)
            df = df.assign(score = sums)
            # on ordonne le df par score decroissant et on recupere les N premiers index
            index_doc = df.sort_values(by="score", axis =0, ascending=False).loc[:,"score"][:N].index.tolist()
            return [self.url[i] for i in index_doc]
        
    def wordCloud(self,numDoc):
        '''
        Affiche un nuage de tags pour le document d'indice numDoc.
        L'importance des mots est donne par la mesure tf-idf.
        '''
        wordcloud = WordCloud(background_color = 'white', max_words = 50).generate_from_frequencies(self.data.T.iloc[:,numDoc])
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.show()
    
    def nMostSimilar(self,numDoc, N):
        '''
        Renvoi les titres des N documents les plus similaires au document d'indice numDoc
        '''
        # similarite cosinus entre chaque document
        m_sim =  cosine_similarity(self.data)
        # liste des indices des documents les plus similaires
        # on prend N+1 car il figurera dans la liste le titre du document numDoc, qu'on souhaite comparer
        l_indexes = m_sim[numDoc].argpartition(-(N+1))[-(N+1):]
        
        return [self.title[i] for i in l_indexes]
        

################################################################################
# Corps principal du programme :
print("*"*100 + "\nPARTIE 2 / Travail d'analyse") 

with open("nature_geo.pick", 'rb') as pickFile :
    doc = pickle.load(pickFile)

# [print(art) for art in doc]
mots_vides = []
with open("stopwords.txt",'r',encoding='utf8') as textFile :
    for ligne in textFile :
        mot = ligne.split("\n")[0].strip()
        if mot != "":
            mots_vides.append(mot)
print("Liste des mots outils : \n",mots_vides, "\n Nombre de mots outils : ",len(mots_vides))

maDTM = DTM(doc, mots_vides)

# test de la methode queryScore
print("QUESTION 1\nTESTS DE LA METHODE queryScore : \n")
print("- Mots valides + minuscle :\n",maDTM.queryScore("alive horrific lifelong bordering area",5)) # OK
print("- Mots valides + majuscule :\n", maDTM.queryScore("alive horrific lifelong bordering Area",5)) # OK : meme resultats que requete sans majuscule
print("- Mots valides + ponctuation :\n", maDTM.queryScore("alive horrific lifelong bordering àrea",5)) # OK : liste vide
print("- Requete vide :\n", maDTM.queryScore("",5)) # OK : liste vide

# test de la methode wordCloud
print("QUESTION 2\nTESTS DE LA METHODE wordCloud : \n")
maDTM.wordCloud(1)

# test de la methode nMostSimilar
print("QUESTION 2\nTESTS DE LA METHODE nMostSimilar : \n")
doc = 33
N = 5 
sim = maDTM.nMostSimilar(doc,N)
print("Titre des {} documents les plus similaires au document {} : {} ".format(N,sim[-1], sim[0:-1] ))