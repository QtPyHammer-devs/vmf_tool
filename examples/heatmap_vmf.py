#!/usr/bin/env python3
"""heatmaps.tf .vmf converter"""
import copy
import json
import urllib.request
import sys
sys.path.insert(0, '../')
import vmf_tool

# http://heatmaps.tf/api.html
heatmap_site = 'http://heatmaps.tf/data/kills/'
url_tail = '.json?fields=killer_class,killer_x,killer_y,killer_z,victim_class,victim_x,victim_y,victim_z,team,killer_weapon'

print('Loading Client Schema...', end='')
schema = vmf_tool.dict_from(open('tf2_client_schema')) # Load Weapon IDs from Client Schema
schema.items_game.items['-1'] = vmf_tool.namespace_from({'name': 'Sentrygun'})
schema.items_game.items['-2'] = vmf_tool.namespace_from({'name': 'Mini-Sentry'})
print(' Done!')

def heatmap_vmf(heatmap, into_vmf='../mapsrc/blank.vmf', victims=True, killers=True, limit=None):
    """Takes a map name (e.g. cp_5days_a2) & creates a file from heatmaps.tf data"""
    try:
        base_vmf = vmf_tool.dict_from(open(into_vmf))
    except IOError:
        raise RuntimeError(f"Couldn't load {into_vmf} to inject props")
    # check to see if file already has visgroups
    base_vmf['visgroups'] = {}
    base_vmf['visgroups']['visgroups'] = [{'name': 'Heatmap', 'visgroupid': '64', 'color': '255 0 255',
                                           'visgroups': [{'name': 'Victims', 'visgroupid': '65', 'color': '0 255 255'},
                                                         {'name': 'Killers', 'visgroupid': '66', 'color': '255 255 0'}]}]

    heatmap = json.load(heatmap)
    k_team = heatmap['fields'].index('team') # 0 = teamless, 1 = spectator, 2 = red, 3 = blu
    k_class = heatmap['fields'].index('killer_class')
    k_wep = heatmap['fields'].index('killer_weapon')
    k_x = heatmap['fields'].index('killer_x')
    k_y = heatmap['fields'].index('killer_y')
    k_z = heatmap['fields'].index('killer_z')
    v_class = heatmap['fields'].index('victim_class')
    v_x = heatmap['fields'].index('victim_x')
    v_y = heatmap['fields'].index('victim_y')
    v_z = heatmap['fields'].index('victim_z')

    ENGINEER = 9
    DEMOMAN = 4
    HEAVY = 6
    MINI_SENTRY = -2
    MEDIC = 5
    PYRO = 7
    SCOUT = 1
    SENTRY = -1
    SNIPER = 2
    SOLDIER = 3
    SPY = 8
    WORLD = 0

    class_name = {SCOUT: 'scout', SOLDIER: 'soldier', PYRO: 'pyro',
                   DEMOMAN: 'demo', HEAVY: 'heavy', ENGINEER: 'engineer',
                   MEDIC: 'medic', SNIPER: 'sniper', SPY: 'spy',
                  WORLD: 'Za Warudo'}
    class_model = {k: f'models/player/{v}.mdl' for k, v in class_name.items()}
    for i, tf_class in class_name.items():
        base_vmf['visgroups']['visgroups'][0]['visgroups'].append({'name': f'{tf_class.capitalize()} Kills', 'visgroupid': str(66 + i)})

    # Hammer automatically fills in missing values
    prop_static = {'classname': 'prop_static', 'editor': {}}

    props = []
    try:
        ent_id = max([e['id'] for e in base_vmf['entities']])
    except:
        ent_id = 0
        
    if limit is None:
        limit = heatmap['map_data']['kill_count']
    for kill in heatmap['kills']:
        kw_id = kill[k_wep]
        try:
            kw_name = f'{schema.items_game.items[kw_id].name} ({kw_id})'
        except:
            kw_name = f'UNKNOWN ({kw_id})'
        
        victim = copy.deepcopy(prop_static)
        victim['id'] = ent_id
##        victim['editor']['logicalpos'] = f'[0 {1000 + ent_id}]'
        ent_id += 1
        victim['model'] = class_model[kill[v_class]]
        victim['origin'] = f'{kill[v_x]} {kill[v_y]} {kill[v_z]}'
        victim['skin'] = '0' if kill[k_team] - 2 == 1 else '1'
        victim['editor']['comments'] = f'Killed by {class_name[kill[k_class]]} @ {kill[v_x]} {kill[v_y]} {kill[v_z]} with {kw_name}'
        victim['editor']['visgroupid'] = '"\n\t\t"visgroupid" "'.join(['64', '65', str(66 + kill[k_class])])
        if kill[k_class] == WORLD:
            victim['editor']['comments'] = f'Killed by WORLD'
            victim['angles'] = f'180 0 0'
            new_origin = [float(x) for x in victim['origin'].split()]
            new_origin[2] += 72
            victim['origin'] = ' '.join(map(str, new_origin))
            props.append(victim)
            continue
        props.append(victim)
        if ent_id >= limit:
            break

        if kill[k_class] != WORLD:
            killer = copy.deepcopy(prop_static)
            killer['id'] = ent_id
##            killer['editor']['logicalpos'] = f'[0 {1000 + ent_id}]'
            ent_id += 1
            killer['model'] = class_model[kill[k_class]]
            killer['skin'] = str(kill[k_team]) # 0 = red, 1 = blue, 2 = uber_red, 3 = uber_blue
            if kill[k_class] == ENGINEER:
                if kill[k_wep] == SENTRY:
                    killer['model'] = 'models/buildables/sentry3.mdl'
                    skin = str(kill[k_team] - 2)
                elif kill[k_wep] == MINI_SENTRY:
                    killer['model'] = 'models/buildables/sentry1.mdl'
                    skin = str(kill[k_team])
            killer['origin'] = f'{kill[k_x]} {kill[k_y]} {kill[k_z]}'
            killer['editor']['comments'] = f'Killed {class_name[kill[v_class]]} @ {kill[k_x]} {kill[k_y]} {kill[k_z]} with {kw_name}'
            killer['editor']['visgroupid'] = '"\n\t\t"visgroupid" "'.join(['64', '66', str(66 + kill[k_class])])
            props.append(killer)
            if ent_id >= limit:
                break

    base_vmf['entities'] = props
    return base_vmf


def get_heatmap(filepath, filter=lambda k: True):
        """Foolproof heatmap generator"""
        filepath = filepath.replace('\\', '/')
        if '/' in filepath:
            outdir, sep, map_name = filepath.rpartition('/')
            outdir = outdir + sep
        else:
            map_name, period, filetype = filepath.rpartition('.')
            if map_name == '':
                map_name = filetype
                filetype = ''
            outdir = ''
        if filetype == 'json': # user downloaded .json
            heatmap = open(filepath) # may lack fields converter needs (see url_tail)
        else: # file named same as map OR map name
            heatmap = urllib.request.urlopen(f'{heatmap_site}/{map_name}{url_tail}')
        heatmap = heatmap_vmf(heatmap) # CONVERSION
        vmf_tool.export(heatmap, open(f'{outdir}{map_name}_heatmap.vmf', 'w'))
        

if __name__ == "__main__":
##    # tell user which maps could not be heatmapped
##    # heatmap.tf/data/maps.json only lists maps with valid overiews
##    # heatmaps.tf API has rate limit of 20 requests per second per client
##    import argparse
##    # MUCH OF THIS IS NOT YET IMPLEMENTED
##    # BUT IS PLANNED TO BE
##    parser = argparse.ArgumentParser(description='Generate .vmf(s) from heatmaps.tf data', epilog="'@presets.txt' will load args from presets.txt", argument_default=[])
##    # --verbose?
##    parser.add_argument('-V', '--version', action='version', version='heatmap to vmf 1.0')
##    CLASSES = ['WORLD', 'SCOUT', 'SOLDIER', 'PYRO', 'DEMO', 'HEAVY', 'ENGY', 'MEDIC', 'SNIPER', 'SPY']
##    parser.add_argument('-filter-class', metavar='CLASS', action='append',
##                        help='pairs with CLASS', choices=CLASSES)
##    parser.add_argument('-filter-not-class', metavar='CLASS', action='append',
##                        help='ignore pairs containing CLASS', choices=CLASSES)
##    parser.add_argument('-filter-killer', metavar='CLASS', action='append',
##                        help='killer_class must be CLASS', choices=CLASSES)
##    parser.add_argument('-filter-victim', metavar='CLASS', action='append',
##                        help='victim_class must be CLASS', choices=CLASSES)
##                        # victim class cannot be WORLD
##    parser.add_argument('-filter-weapon', metavar='WEAPON', action='append',
##                        help='sampled from latest tf2 item schema')
##    # -filter-custom-kill STATE
##    # -filter-death-flag FLAG
##    # instead of choices use: argparse.ArgumentError('WEAPON not found in client schema')
##    # filter also weapon slots
##    # some -filters will need additional fields in .json (modify url_tail)
##    # use latest TF2 Client Item Schema (download or check vpk)
##    parser.add_argument('-filter-range', metavar='RANGE', action='append', type=float,
##                        help='pairs  >= RANGE units apart (inverted if negative)')
##    # --filter-robot (names from mvm .pop files?)
##    # would require -pop POPFILE
##    parser.add_argument('--limit', type=int,
##                        help='stop at LIMIT props (per map)')
##    parser.add_argument('--out-folder', metavar='FOLDER', default='',
##                        help='put generated .vmf(s) in this folder')
##    hard_filters = parser.add_mutually_exclusive_group()
##    hard_filters.add_argument('--only-killers', action='store_false', dest='killers',
##                              help='list only killers')
##    hard_filters.add_argument('--only-victims', action='store_false', dest='victims',
##                              help='list only victims')
##    parser.add_argument('--inject-vmf', metavar='VMF', # if not None: outfile = infile
##                        help='inject ALL heatmaps into this .vmf')
##    parser.add_argument('map', nargs='*', action='append', # raise ArgumentError if no map or folder
##                       help="generate .vmf for each map's heatmap")
##    parser.add_argument('-folder', metavar='FOLDER', action='append', dest='folders', # if not None: os.listdir() ...
##                       help='generate .vmf for each map in FOLDER')
##
##    # TEST ARGS
##    parser.print_help() # PRINT PRETTIER
##    args = parser.parse_args('koth_campania_a11 -filter-class SOLDIER -filter-class DEMO'.split())
##    print(args)
##    
##    # for i, f in enumerate(folders):
##    #     try:
##    #         folders[i] = [x for x in os.listdir(f) if x.endswith('.vmf')]
##    #     except:
##    #        raise argparse.ArgumentError(f'{f} is not a valid folder')
##    # args.maps = itertools.chain(args.maps, *folders)
##    #
##    # if args.out_folder is not None:
##    #     if not os.isdir(args.out_folder):
##    #         raise argparse.ArgumentError('OUT_FOLDER is not a folder!')
##    #
##    # create filter function for .json(s)
##    # lambda k: all(any([k[field] == (a or b), ...]), ...)
##    #
##    # filter_weapons = any([??? for w in filter_weapons])
    #TEMPORARY DRAG & DROP
    import sys
    for filepath in sys.argv[1:]:
        print(filepath)
        get_heatmap(filepath)
    
    
