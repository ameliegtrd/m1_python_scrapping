# -*- coding: utf-8 -*-

################################################################################
# fichier  : scrapping.py
# Auteur : GOUTARD Amelie
################################################################################

''' 
Theme : Nature & Geography/Disasters/Extreme Weather 
Lien : https://www.thecanadianencyclopedia.ca/en/browse/things/nature-geography/disasters-extreme-weather?type=article
''' 

################################################################################
# Importation de fonctions externes :
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, Tag, NavigableString
import pickle
from multiprocessing import Pool, cpu_count

################################################################################
# Definition locale de fonctions :

def maybeMakeNumber(s):
    '''
    Retourne une chaine 's' en nombre entier si possible ou 0 sinon 
    '''
    if not s:
        return s
    try:
        f = float(s)
        i = int(f)
        # si c'est un float retourne 0
        return i if f == i else 0
    # si ce n'est pas possible d'appliquer int() ou float() (i.e un string) retourne 0
    except ValueError:
        return 0

def listeURL(mon_url):
    '''
    Parse le lien html et stocke les liens des articles dans une liste
    '''
    # ouvrir avec urlopen mon_url
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    req = Request(mon_url,headers={'User-Agent':user_agent})
    
    # gestion des exceptions avec un bloc try/except
    try: 
        html = urlopen(req)
    except (HTTPError, URLError) as e:
        sys.exit(e) # sortie du programme avec affichage de l’erreur
    
    # on parse la page html en utilisant le parser de lxml
    bsObj = BeautifulSoup(html, "lxml")
    
    # on recupere le nombre de pages
    liste_npage = []
    for ul in bsObj.find_all("ul", class_="pagination"):
        for li in ul.find_all("li"):
            a = li.find("a", class_="page-link")
            # on recupere le texte (=numero de page) de la balise a, seulement si elle existe
            if a is not None:
               liste_npage.append(a.text)
            
    # on garde uniquement les nombres de la liste qu'on convertit ensuite en int puis on prend le maximum
    # i.e le nombre de pages necessaires pour recuperer tous les articles
    nb_page = max(map(maybeMakeNumber,liste_npage))
    #print(nb_page)
    
    # pour chaque page correspondant a la recherche on recupere les liens des articles
    liste_url = []
    for page in range(1,nb_page+1):
        # on parcours les pages
        mon_url = mon_url+"&page="+str(page)
        #print(mon_url)
        req = Request(mon_url,headers={'User-Agent':user_agent})
        try: 
            html = urlopen(req)
        except (HTTPError, URLError) as e:
            sys.exit(e)
        # on parse la page html en utilisant le parser de lxml    
        bsObj = BeautifulSoup(html, "lxml")
        # on stocke les liens des articles dans une liste
        for div in bsObj.find_all("div", class_="search-single-info"):
            liste_url.append(div.find("a")["href"])
    
    return(liste_url)


def parseURL(mon_url):
    '''
    Parse l'url d'un article et renvoie dans un tuple son l'url, son titre et son texte
    '''
    # ouvrir avec urlopen mon_url
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    req = Request(mon_url,headers={'User-Agent':user_agent})
    
    # gestion des exceptions avec un bloc try/except
    try: 
        html = urlopen(req)
    except (HTTPError, URLError) as e:
        sys.exit(e) # sortie du programme avec affichage de l’erreur
    
    # on parse la page html en utilisant le parser de lxml
    bsObj = BeautifulSoup(html, "lxml")
    
    # on recupere le titre de l'article
    titre = bsObj.find("h1").get_text(strip=True)
    # on recupere le contenu de l'article
    masque = bsObj.find("div", id="article-content-def")
    # uniquement le contenu de l'article qui nous interesse
    texte = getSelectedText(masque)
    
    return(mon_url,titre,texte)


def getSelectedText(montag):
    '''
    Prend en parametre un objet Tag et, s'il est valide, 
    renvoie le texte contenu dans ce Tag et dans tous ses descendants valides
    '''
    texte = ""
    # boucle sur les enfants de monTag
    for c in montag.children:
        # si l'enfant est un NavigableString : on recupere le texte
        # dans c.string, et on retire les espaces en trop (.strip())
        if type(c) == NavigableString:
            texte += " "+(c.string).strip()
        # si l'enfant est un tag et qu'il est valide, on va chercher le texte a l'interieur
        # et on le rajoute au texte deja recupere
        elif type(c) == Tag and validTag(c):
            texte += getSelectedText(c)
    return texte


def validTag(tag):
    '''
    Prend en parametre un objet Tag et renvoie un booleen indiquant si ce Tag est valide ou pas
    (si il correspond bien au contenu souhaite de l'article)
    '''
    if tag.name == "img" or tag.name=="h3" or tag.name == "figcaption" or tag.name == "a" or tag.name == "sup" :
        return False
    if "class" in tag.attrs :
        # on parcours toutes les class
        for elem in tag.attrs["class"]:
            if elem in ['slider', 'bxslider', 'bxslider-controls']:
                return False
    return True



# page avec plusieurs pages https://www.thecanadianencyclopedia.ca/en/browse/things/business-economics

################################################################################
# Corps principal du programme :

if __name__ == '__main__' :
    print("PARTIE 1 / Corpus analysé") 

    url = "https://www.thecanadianencyclopedia.ca/en/browse/things/nature-geography/disasters-extreme-weather?type=article"
    # on recupere les liens des articles 
    liste_url = listeURL(url)
    print("*"*100 , "Liens des articles : " , liste_url , "\n Nombre d'articles : " , len(liste_url))

    # on recupere pour chaque article son url, titre et texte
    with Pool(cpu_count()-1) as p :
        res = p.map(parseURL,liste_url)
    print("*"*100 , "\n  Pour le premier article :  \n - URL : {} \n - Titre  : {} \n - Texte : {} ".format(res[0][0], res[0][1], res[0][2]))

    # on stocke le resultat dans une liste et on dump le resultat dans un fichier pickle        
    with open('nature_geo.pick', 'wb') as pickFile:
         pickle.dump(res, pickFile)
