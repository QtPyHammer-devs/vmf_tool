#!/usr/bin/env python3.6
"""Drag and drop a .vmf or .bsp that has been tested on a tf2maps.net server
this script will attempt to find the appropriate heatmap and generate a vmf.
OR `python3.6 heatmap_vmf.py map_name` in terminal"""
#TODO: special filtering (e.g. draw lines on long sightlines)
#TODO: filters for distance and class
import json
import urllib.request
import sys
sys.path.insert(0, '../')
import vmf_tool

def heatmap_vmf(map_name, outdir=''):
    """Takes a map name (e.g. koth_test_a1) & creates a file from heatmaps.tf data"""
    try:
        base_vmf = vmf_tool.vmf_to_dict(open('../mapsrc/blank.vmf'))
    except IOError:
        raise RuntimeError("Couldn't load blank.vmf to inject props")

    # http://heatmaps.tf/api.html
    heatmap_site = 'http://heatmaps.tf/data/kills'
    url_tail = '.json?fields='
    url_tail += ', '.join(['killer_class', 'killer_x', 'killer_y', 'killer_z',
                           'victim_class', 'victim_x', 'victim_y', 'victim_z',
                           'team', 'killer_weapon'])
    # currently enounters 502 Bad Gateway Error
    heatmap = urllib.request.urlopen(f'{heatmap_site}{map_name}{url_tail}')
    heatmap = json.load(heatmap)

    k_team = heatmap['fields'].index('killer_team')
    # 0 = teamless, 1 = spectator, 2 = red, 3 = blu
    # 0 = red, 1 = blue, 2 = uber_red, 3 = uber_blue
    k_class = heatmap['fields'].index('killer_class') # negative = building
    k_wep = heatmap['fields'].index('killer_weapon')
    k_x = heatmap['fields'].index('killer_x')
    k_y = heatmap['fields'].index('killer_y')
    k_z = heatmap['fields'].index('killer_z')
    v_class = heatmap['fields'].index('victim_class')
    v_x = heatmap['fields'].index('victim_x')
    v_y = heatmap['fields'].index('victim_y')
    v_z = heatmap['fields'].index('victim_z')

    MINI_SENTRY = -2
    SENTRY = -1
    WORLD = 0
    SCOUT = 1
    SNIPER = 2
    SOLDIER = 3
    DEMOMAN = 4
    MEDIC = 5
    HEAVY = 6
    PYRO = 7
    SPY = 8
    ENGINEER = 9

    class_model = {SCOUT: 'scout.mdl', SOLDIER: 'soldier.mdl', PYRO: 'pyro.mdl',
                   DEMOMAN: 'demo.mdl', HEAVY: 'heavy.mdl', ENGINEER: 'engineer.mdl',
                   MEDIC: 'medic.mdl', SNIPER: 'sniper.mdl', SPY: 'spy.mdl'}
    class_model = {k: f'models/player/{v}' for k, v in class_model.items()}

    # would hammer autofill missing values?
    prop_static = {'classname': 'prop_static',
                   'angles': '0 0 0', # face partners?
                   'fademindist': '-1', 'fadescale': '1',
                   'lightmapresolutionx': '32', 'lightmapresolutiony': '32',
                   'editor': {'colour': '255 255 255', 'visgroupshown': '1',
                              'visgroupautoshown': '1',
                              'logicalpos': '[0 -1]'}} # what is logicalpos?

    props = []
    ent_id = 0
    for kill in heatmap['kills']:
        if kill[k_class] == WORLD:
            continue # skip hazards / falls
        killer = prop_static.copy()
        killer['id'] = ent_id
        ent_id += 1
        killer['model'] = class_model[kill[k_class]]
        killer['skin'] = str(kill[k_team])
        if kill[k_class] == ENGINEER:
            if kill[k_wep] == SENTRY:
                killer['model'] = 'models/buildables/sentry2.mdl'
                skin = str(kill[k_team] - 2)
            elif kill[k_wep] == MINI_SENTRY:
                killer['model'] = 'models/buildables/sentry1.mdl'
                skin = str(kill[k_team])
        killer['origin'] = f'{kill[k_x]} {kill[k_y]} {kill[k_z]}'
        # visgroup = killers
        props.append(killer)
                
        victim = prop_static.copy()
        victim['id'] = ent_id
        ent_id += 1
        victim['model'] = class_model[kill[v_class]]
        victim['origin'] = f'{kill[v_x]} {kill[v_y]} {kill[v_z]}'
        victim['skin'] = '0' if kill[k_team] - 2 == 1 else '1'
        # visgroup = victims
        props.append(victim)

    base_vmf['entities'] = props
    outdir = outdir.replace('\\', '/').strip()
    outdir += '/' if not (outdir == '' or outdir.endswith('/')) else ''
    vmf_tool.export_vmf(base_vmf, open(f'{outdir}{map_name}_heatmap.vmf', 'w'))

if __name__ == "__main__":
    import sys
    heatmap_vmf('koth_campania_a11')
    for filepath in sys.argv[1:]:
        filepath = filepath.replace('\\', '/')
        outdir, sep, map_name = filepath.rpartition('/')
        map_name = map_name.rpartition('.')[0]
        heatmap_vmf(map_name, outdir)
