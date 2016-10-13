import shelve
import requests
import requests_cache

#cache = requests_cache.backends.sqlite.DbCache('leafly_cache')
#requests_cache.install_cache('leafly_cache')

root = "https://www.leafly.com"
headers =  {'accept': 'application/json'}

def dump_strains():
    """ fetch strains catalogue """

    all_strains = []
    url = "%s/explore/sort-alpha" % root
    islastpage = False
    
    def isStrain(strain):
        validators = [
          strain is not None,
          type(strain) == dict,
          strain['DisplayCategory'] != "Edible",
          'Name' in strain,   
        ]
        return all(validators)
        
        
    while islastpage == False:

        print "requesting %s " % url
        
        r = requests.get(url, headers=headers)

        data = r.json()
        model = data['Model']

        url = "%s%s" % (root, model['NextPageUrl'])
        islastpage = model['PagingContext']['IsLastPage']         
        strains = filter( isStrain, model['Strains'] )

        all_strains.extend(strains)

        print "adding %s strains (%s), %s in db" % ( len(strains), len(model['Strains']), len(all_strains) )
    
    return all_strains


def expand_strains(strains):
    """
    get json data for each strain.
    ( lignage, effects, comments, rating ... )
    
    DisplayCategory in [ Hybrid sativa indica ]
    url = https://www.leafly.com/DisplayCategory/UrlName
    """
    
    strains.sort( key=lambda x : x['Name'] , reverse=True )
    
    for s in strains:
        #print s['Name']
        url = "%s/%s/%s" %( root, s['DisplayCategory'], s['UrlName'])
        print "requesting %s " % url
        try : 
            r = requests.get(url, headers=headers)
            s['page'] = r.json()
        except :
            print "error"
    return strains

def saveAs(strains, path):
    """ saves strains to a shelve db """
    db = shelve.open(path)    
    for strain in strains:
        db[str(strain['UrlName'])] = strain
    db.close()