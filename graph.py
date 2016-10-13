import shelve

path = "./strains.db"

STRAIN_PROPS = [ 'sativa', 'name', 'indica', 'url', 'urlname', 'symbol', 'abstract',
                 'shape', 'label']
STRAIN_TYPES = dict([ ('Indica', 'circle'),('Sativa','triangle'),( 'Hybrid', 'square') ])


def parse(path):
    """ 
    :param path:  shelve db path
    """
    
    db = shelve.open(path)
    print len(db)

    with_parents = 0

    p_strains  = {}

    strains = {}

    for row in db.itervalues():
        if 'page' in row:
            
            strain = {
                        'name' : row['Name'],
                        'label' : row['UrlName'],
                        'urlname' : row['UrlName'],
                        'symbol' : row['Symbol'], 
                        'category' : row['Category'], 
                        'shape' : STRAIN_TYPES[row['Category']], 
                        'url' : "%s/%s" % ( row['Category'], row['UrlName'] ) , 
                        'abstract' : row['page'].get('Abstract', ""),
                        'indica' : row['page'].get('PercentIndica', ""),
                        'sativa' : row['page'].get('PercentSativa', ""),
                        'parents' : row['page']['Model']['Strain'].get('Parents', []),
                    }
                    
            strains[strain['urlname']] = strain

        else : print "ERROR", row 
    
    for strain in strains.itervalues():
        parents = strain['parents']
        if len(parents):
            with_parents += 1
            for p in parents:
                _id = p['Slug']
                #if name in syns: name = syns[name]
                if _id in strains:
                    p_strains[_id] = p_strains.get( _id , 0) + 1
                else :
                    print strain['urlname'], p['Slug']

    # print some stuff
    print( "parents",  with_parents, len(p_strains))
    l1 = list(set(p_strains.values()))
    print len(l1), sorted(l1)[-10:]
    s1 =  set(p_strains.keys()).difference(set(strains.keys()))
    s2 =  set(strains.keys()).difference(set(p_strains.keys()))
    print len(s1), len(s2), s1 

    print( "len", len(strains),
           len(set([ e['urlname'] for e in strains.itervalues()]))
         )
    return strains


def to_graph(strains, star=0):
        
    import igraph
    from cello.graphs.prox import prox_markov_dict, sortcut, ALL

    vs = strains.values()
    invidx = sorted([ v['urlname'] for v in vs ])
    vidx = dict( (e,i) for i,e in enumerate(invidx) )
    vattrs = { 'label': [ v.encode('UTF8') for v in invidx] }
    starred = []
    
    at = lambda x : vidx[x]
    edges = [ (at(e['Slug']), at(v['urlname']) ) for v in vs for e in v['parents']   ]
    es = dict(zip( edges , [0] * len(edges) ))
   
    ettrs = {}
    
    graph = igraph.Graph(directed= False, 
                     graph_attrs={},
                     n=len(invidx),
                     vertex_attrs=vattrs,
                     edges=edges,
                     edge_attrs=ettrs)
                     
    print graph.summary()

    if star:
        # Extract n prox vertex
        cut = star; length = 50
        extract = prox_markov_dict(graph, range(graph.vcount()), length, add_loops=True)
        print "star" , star, extract
        subvs =  [ i for i,v in sortcut(extract,cut)]

        g = graph.subgraph( subvs )
        starred = (g.vs["label"])

    graph.vs['starred'] = [ v in starred for v in graph.vs['label'] ]
    print starred
    
    return graph

def post(gid, graph, strains, host, key, star=0):

    from botapi import Botagraph, BotApiError
    from reliure.schema import Doc, Schema
    from reliure.types import Text, Numeric , Boolean, GenericType

    bot = Botagraph(host, key)


    print gid, "exists",  bot.has_graph(gid)
    
    if not bot.has_graph(gid) :
        print "\n * Create graph %s" % gid
        bot.create_graph(gid, { 'description':"Cannabis strains from leafly.com",
                                'image': "",
                                'tags': ['cannabis', 'strains']
                              }
                        )
                        
    print "\n * Get schema '%s'" % gid
    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    print "\n nodetypes: ", nodetypes.keys()
    print "\n edgetypes: ", edgetypes.keys()

    for k,v in STRAIN_TYPES.iteritems():
        if not k in nodetypes:
            props = {  e : Text() for e in STRAIN_PROPS }
            print k,v
            bot.post_nodetype(gid, k,  "%s strain"% v , props)

    if not "has_child" in edgetypes:
        print "\n\n * Creating edge type %s" % "has_parent"
        bot.post_edgetype(gid, "has_child", "strain has another strain as child", {"a":Text()})

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }

    print nodetypes
    print edgetypes

    print "* Posting nodes"

    idx = {}
    fail = 0; count = 0
    to_star = set([ v['label'] for v in graph.vs if v['starred']  ][:star] )
    to_star_uuids = set()
     
    def gen_nodes():
        for vertex in graph.vs:
            _id = vertex['label']
            strain = strains[_id]
            yield {
                'nodetype': nodetypes[strain['category']]['uuid'],
                'properties': { k: strain[k] for k in STRAIN_PROPS } 
               }
               
    for node, uuid in bot.post_nodes( gid, gen_nodes() ):
        if not uuid:
            fail += 1
        else :
            count += 1
            idx[node['properties']['label']] = uuid
            if node['properties']['label'] in to_star :
                to_star_uuids.add(uuid)
                
    print "%s (%s failed) nodes inserted " % (count, fail)

    print "* Starring %s nodes" % len(to_star_uuids)
    print to_star
    bot.star_nodes(gid, list(to_star_uuids))


    
    print "* Posting edges"

    inv_idx = { v:k for k,v in idx.iteritems() }
    fail = 0; count = 0

    def gen_edges():
        for edge in graph.es:
            src = graph.vs[edge.source]['label']
            src = idx[src]

            tgt = graph.vs[edge.target]['label']
            tgt = idx[tgt]
            
            yield {
                    'edgetype': edgetypes['has_child']['uuid'],
                    'source': src,
                    'label' : "has_child",
                    'target': tgt,
                    'properties': {}
                  }
    
    for obj, uuid in bot.post_edges( gid, gen_edges() ):
        if not uuid:
            fail += 1
        else :
            count += 1
    print "%s (%s failed) edges inserted " % (count, fail)
