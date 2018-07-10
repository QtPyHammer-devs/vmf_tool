#!/usr/bin/env python3.6
"""Drag and drop a .vmf or .bsp that has been tested on a tf2maps.net server
this script will attempt to find the appropriate heatmap and generate a vmf.
OR `python3.6 heatmap_vmf.py map_name` in terminal"""
#TODO: cleaner argument handling when called in console (drag & drop too)
import json
import sys
sys.path.insert(0, '../')
import vmf_tool

def heatmap_vmf(heatmap):
    """Takes a map name (e.g. koth_test_a1) & creates a file from heatmaps.tf data"""
    try:
        # once visgroups are understood, allow injection
        base_vmf = vmf_tool.vmf_to_dict(open('../mapsrc/blank.vmf'))
    except IOError:
        raise RuntimeError("Couldn't load blank.vmf to inject props")

    heatmap = json.load(heatmap)
    k_team = heatmap['fields'].index('team')
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

    # killer_weapon
    MINI_SENTRY = -2
    SENTRY = -1
    # *_class
    WORLD = 0 # fall / hazard / non-player
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
                   'angles': '0 0 0', # bow to your partner. do-si-do
                   'fademindist': '-1', 'fadescale': '1',
                   'lightmapresolutionx': '32', 'lightmapresolutiony': '32',
                   'editor': {'colour': '255 255 255', 'visgroupshown': '1',
                              'visgroupautoshown': '1',
                              'logicalpos': '[0 -1]'}} # what is logicalpos?

    props = []
    ent_id = 0
    for kill in heatmap['kills']:
        if kill[k_class] == WORLD:
            continue # how should environmental deaths be communicated?
        killer = prop_static.copy()
        killer['id'] = ent_id
        ent_id += 1
        killer['model'] = class_model[kill[k_class]]
        killer['skin'] = str(kill[k_team])
        if kill[k_class] == ENGINEER:
            if kill[k_wep] == SENTRY:
                killer['model'] = 'models/buildables/sentry3.mdl'
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
    return base_vmf

if __name__ == "__main__":
    import urllib.request
    # http://heatmaps.tf/api.html
    heatmap_site = 'http://heatmaps.tf/data/kills/'
    url_tail = '.json?fields=killer_class,killer_x,killer_y,killer_z,' \
               'victim_class,victim_x,victim_y,victim_z,team,killer_weapon'
    # check heatmap.tf/data/maps.json for each mapname
    # download once & log maps that could not be heatmapped
    import sys
    # ARGPARSE
    # -folder [FOLDER]: get heatmap for every .bsp or .vmf in folder (once each)
    # -filter class [CLASS]: show deaths and kills for CLASS only
    # -filter killer_class [CLASS]: show pairs where CLASS killed
    ## CLASS includes WORLD, HAZARD, TRAIN, FALL, SAWBLADE, DROWN etc.
    # -filter victim_class [CLASS]: show pairs where CLASS died
    # -filter range [RANGE]: only kills >RANGE (<RANGE if negative)
    # -filter remove [FILTER]: remove a filter (same representaion as previous)
    ## -filter can be called multiple times (CAN ARGPARSE DO THIS?)
    ## -filter changes state, and applies only to maps after it in *args
    ## -filter is 3 consecutive args, unless it is 'remove' (which is 4)
    # -limit [LIMIT]: do not write more than LIMIT pairs
    # -only-killers
    # -only-victims
    # -filter area [MINS] [MAXS]: only pairs >MINS & <MAXS
    ## [MINS] = (X Y Z), [MAXS] = (X Y Z)
    #
    # IMPLEMENTATION
    # filters = {class: {killer: [], victim: []}, area: [], range: []}
    # for arg in args:
    #     if '-filter' in arg:
    #         ,,,
    #         filters[filter_type].append(filter_args)
    #     else: # heatmap
    #         ,,,
    #         heatmap_vmf(heatmap, filters)
    #
    # INSIDE HEATMAP_VMF()
    ## convert filters to lambdas?
    # for kill in heatmap['kills']:
    #    if all([... for f in filters]): # any() for each key
    ## "-filter killer_class" all(any(k[k_class] in [...], k[v_class] in [...]))
    ## "-filter class" k[k_class] in [...] or k[v_class] in [...]
    ## for '-filter class' only CLASS is shown (not paired killer / victim)
    #        props.append(...)
    sys.argv.append('koth_campania_a11') # TEST
    for filepath in sys.argv[1:]:
        filepath = filepath.replace('\\', '/')
        if '/' in filepath:
            outdir, sep, map_name = filepath.rpartition('/')
        else:
            map_name = filepath
            outdir = ''
        if map_name.endswith('.json'): # user downloaded .json
            heatmap = open(filepath) # needs fields requested in url_tail
        else: # file named same as map OR map name in terminal
            if '.' in map_name:
                map_name = map_name.rpartition('.')[0]
            heatmap = urllib.request.urlopen(f'{heatmap_site}{map_name}{url_tail}')
        heatmap = heatmap_vmf(heatmap) # CONVERSION
        vmf_tool.export_vmf(heatmap, open(f'{outdir}{map_name}_heatmap.vmf', 'w'))
