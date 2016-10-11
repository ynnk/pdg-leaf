# pdg-leaf
graph of cannabis strain

## Leafly API 
None is available, but one can request json data exploring strains

### Explore paginated strains

There is about 2100 strains in db
  
  $ curl  https://www.leafly.com/explore/page-44 -H X-Requested-With:XMLHttpRequest -H accept:application/json

### Get json data for a specfied strain

  $ curl --get https://www.lealy.com/indica/northern-lights -H X-Requested-With:XMLHttpRequest -H accept:application/json



## Dump

$ python dump.py

## Build Graph

## Padagraph Bot

