#!/usr/bin/env python
#-*- coding:utf-8 -*-

USAGE = """
dumps data from https://www.leafly.com

$ python main.py --dump --path db.path

"""
import sys
import argparse
import dump
import graph
        
def main():

    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument("--path", action='store',help="db path to store dump")

    parser.add_argument("--dump", action='store_true', default=False, help="dump")

    parser.add_argument("--parse", action='store_true', default=False, help="parse")
    
    parser.add_argument("--graph", action='store_true', default=False, help="create an summaryze with igraph")

    parser.add_argument("--star", action='store', type=int, default=0, help="star n prox nodes")

    parser.add_argument("--post", action='store', help="post to padagraph", default="")
    parser.add_argument("--host", action='store', help="host", default="http://padagraph.io")
    parser.add_argument("--key", action='store', help="token", default=None)
    
    args = parser.parse_args()

    strains = {}
    sgraph = None
    
    if args.dump:
        strains = dump.dump_strains()
        strains = dump.expand_strains(strains)
        dump.saveAs(strains, args.path)
    
    if args.parse: 
        strains = graph.parse(args.path)

    if args.graph:
        sgraph = graph.to_graph(strains, star=args.star)
        
    if len(args.post):
        graph.post(args.post, sgraph, strains, args.host, args.key, star=args.star)
        
        
if __name__ == '__main__':
    sys.exit(main())


