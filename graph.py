import shelve

path = "./strains.db"

STRAIN_TEXT_PROPS = [ 'label', 'shape', 'image', 'video',          
                 'name','url', 'urlname', 'symbol', 'parents', 'abstract', 'heroimage',
                 'indica', 'sativa', 'height', 'rating'
                ]
STRAIN_MULTI_PROPS = ['Flavors', 'Effects' , 'NegativeEffects', 'GeneralEffects', 'MedicalEffects', 'Symptoms']
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
            model = row['page']['Model']
            strain = model['Strain']
            props = {
                        'label'   : row['UrlName'].replace('-', ' '),
                        'shape'   : STRAIN_TYPES[row['Category']], 

                        'urlname' : row['UrlName'],
                        'symbol'  : row['Symbol'], 
                        'name'    : row['Name'],
                        'category': row['Category'], 
                        'url'     : "%s/%s" % ( row['Category'], row['UrlName'] ) , 
                        'image'    : 'https://d3ix816x6wuc0d.cloudfront.net/%s/%s/badge?width=340' % ( row['Category'], row['UrlName'] ) ,

                        'heroimage': strain.get('HeroImage',''),
                        'video'    : strain.get('VideoUrl',''),
                        'rating'   : strain.get('Rating',''),
                        'height'   : strain.get('Height',''),
                        'indica'   : strain.get('PercentIndica', ""),
                        'sativa'   : strain.get('PercentSativa', ""),
                        'abstract' : strain.get('Abstract', ""),
                        'parents'  : strain.get('Parents', []),
                    }
            props['parents'] = [ e['Slug'] for e in props['parents'] ]
            props.update({ s : [ e['Name'] for e in model[s] ] for s in STRAIN_MULTI_PROPS })
                    
            strains[props['urlname']] = props
            #print props['urlname'],props['parents']

        else : print "ERROR", row 
    
    for strain in strains.itervalues():
        parents = strain['parents']
        if len(parents):
            with_parents += 1
            for p in parents:
                #if name in syns: name = syns[name]
                if p in strains:
                    p_strains[p] = p_strains.get( p , 0) + 1
                else :
                    print strain['urlname'], p

    #print( "parents",  with_parents, len(p_strains))
    l1 = list(set(p_strains.values()))
    #print len(l1), sorted(l1)[-10:]
    s1 =  set(p_strains.keys()).difference(set(strains.keys()))
    s2 =  set(strains.keys()).difference(set(p_strains.keys()))
    #print len(s1), len(s2), s1 

    print( "len", len(strains),
           len(set([ e['urlname'] for e in strains.itervalues()]))
         )
    return strains


def to_graph(strains, star=0):
        
    import igraph
    from cello.graphs.prox import prox_markov_dict, sortcut, ALL

    vs = strains.values()
    #invidx = sorted([ v['urlname'] for v in vs ])
    vattrs = {
     'label': [ v['label'].encode('UTF8') for v in vs],
     'urlname': [ v['urlname'].encode('UTF8') for v in vs]
             }

    vidx = dict( (v['urlname'],i) for i,v in enumerate(vs) )
    invidx = [ v['urlname'] for v in vs ]
    starred = []
    
    at = lambda x : vidx[x]
    edges = [ (at(e), at(v['urlname']) ) for v in vs for e in v['parents']   ]
    #edge_types = [ for v in vs for e in v['parents']   ]

    print("len edges", len(edges))

    #for v in vs :
        #for e in v['parents'] :
            #print e['Slug'], at(e['Slug']), "has_child", v['urlname'] , at(v['urlname']) 
    
    ettrs = {}
    
    graph = igraph.Graph(directed=True, 
                     graph_attrs={},
                     n=len(invidx),
                     vertex_attrs=vattrs,
                     edges=edges,
                     edge_attrs=ettrs)

    print graph.summary()

    #print("clusters", graph.clusters()[10])
    #graph = graph.clusters().giant()
                     
    print graph.summary()


    if star:
        # Extract n prox vertex
        cut = star; length = 50
        extract = prox_markov_dict(graph, range(graph.vcount()), length,mode=ALL, add_loops=True)
        subvs =  [ i for i,v in sortcut(extract,cut)]
        g = graph.subgraph( subvs )
        starred = set(g.vs["label"])
        graph = g
    
    graph.vs['starred'] = [ v in starred for v in graph.vs['label'] ]
    print starred
    
    return graph

def post(gid, graph, strains, host, key, star=0):

    from botapi import Botagraph, BotApiError
    from reliure.schema import Doc, Schema
    from reliure.types import Text, Numeric , Boolean, GenericType

    bot = Botagraph(host, key)

    print gid, "exists",  bot.has_graph(gid)

    
    if bot.has_graph(gid) :
        bot.delete_graph(gid)
    
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

    for k,v in STRAIN_TYPES.iteritems():
        if not k in nodetypes:
            props = {  e : Text() for e in STRAIN_TEXT_PROPS }
            props.update({ e : Text(multi=True, uniq=True) for e in STRAIN_MULTI_PROPS })
            print " * Creating node type `%s` strain" % k
            bot.post_nodetype(gid, k,  "%s strain"% v , props)

    if not "has_child" in edgetypes:
        print " * Creating edge type %s" % "has_child"
        bot.post_edgetype(gid, "has_child", "strain has another strain as child", {})

    schema = bot.get_schema(gid)['schema']
    nodetypes = { n['name']:n for n in schema['nodetypes'] }
    edgetypes = { e['name']:e for e in schema['edgetypes'] }


    idx = {}
    fail = 0; count = 0
    to_star = set([ v['urlname'] for v in graph.vs if v['starred']  ][:star] )
    to_star_uuids = set()
    print to_star
     
    print " * Posting nodes"
    def gen_nodes():

        keys = STRAIN_TEXT_PROPS + STRAIN_MULTI_PROPS

        for vertex in graph.vs:
            _id = vertex['urlname']
            strain = strains[_id]
            yield {
                'nodetype': nodetypes[strain['category']]['uuid'],
                'properties': { k: strain[k] for k in keys } 
               }
               
    for node, uuid in bot.post_nodes( gid, gen_nodes() ):
        if not uuid:
            fail += 1
        else :
            count += 1
            key  = node['properties']['urlname']
            idx[key] = uuid
            if key in to_star :
                to_star_uuids.add(uuid)
                
    print "   %s (%s failed) nodes inserted " % (count, fail)

    print " * Starring %s nodes" % len(to_star_uuids)
    bot.star_nodes(gid, iter(list(to_star_uuids)))


    print " * Posting edges"
    inv_idx = { v:k for k,v in idx.iteritems() }
    fail = 0; count = 0

    def gen_edges():
        for edge in graph.es:
            _src = graph.vs[edge.source]['urlname']
            src = idx[_src]

            _tgt = graph.vs[edge.target]['urlname']
            tgt = idx[_tgt]
            
            yield {
                    'edgetype': edgetypes['has_child']['uuid'],
                    'source': src,
                    'label' : "-",
                    'target': tgt,
                    'properties': {}
                  }
    
    for obj, uuid in bot.post_edges( gid, gen_edges() ):
        if not uuid:
            fail += 1
        else :
            count += 1
    print "   %s (%s failed) edges inserted " % (count, fail)
