#!/usr/bin/env python
#-*- coding:utf-8 -*-

USAGE = """
dumps data from https://www.leafly.com

$ python dump.py

"""
import sys
import argparse
import requests
import requests_cache

cache = requests_cache.backends.sqlite.DbCache('leafly_cache')
requests_cache.install_cache('leafly_cache')

root = "https://www.leafly.com"
headers =  {'accept': 'application/json'}

def dump_strains():

    all_strains = []
    url = "%s/explore/sort-alpha" % root
    islastpage = False
    

    while islastpage == False:

        print "requesting %s " % url
        
        r = requests.get(url, headers=headers)

        data = r.json()
        model = data['Model']

        url = "%s%s" % (root, model['NextPageUrl'])
        islastpage = model['PagingContext']['IsLastPage'] 
        strains = model['Strains']
        strains = filter( lambda x : x['DisplayCategory'] != "Edible", strains )

        all_strains.extend(strains)

        print "adding %s strains, %s in db" % ( len(strains),len(all_strains) )
    

    
    return all_strains


def expand_strains(strains):
    """
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


        
def main():
    """ Function doc
    :param : 
    """
    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument("--option", action='store_true',help="")
    args = parser.parse_args()
    

    strains = dump_strains()
    
    strains = expand_strains(strains)
    
    
if __name__ == '__main__':
    sys.exit(main())


