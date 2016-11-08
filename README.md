# pdg-leaf
graph of cannabis strain

## Leafly API 
None is available, but one can request json data exploring strains

### Explore paginated strains

There is about 2100 strains in db
  
    $ curl  https://www.leafly.com/explore/page-44 -H accept:application/json

### Get json data for a specfied strain
 
    $ curl --get https://www.lealy.com/indica/northern-lights -H accept:application/json

## Install requirements

    $ pip install -r requirements.txt

## Dump

Crawl json data

    $ python main.py --dump --path strains.db

## Build Graph

    $ python main.py --graph --path strains.db 

## Padagraph Bot

### Get a Token

* Log into http://padagraph.io,
* Get your key from http://padagraph.io/account/me/generate_auth_token
* Save it in a txt file `token.txt`

### Post graph

    $ python main.py  --graph --path strains.db --star 100 --post strains --key `cat ../token.txt`

## Exploration

Visit http://padagraph.io/graph/strains
