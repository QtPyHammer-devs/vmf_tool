#!/usr/bin/env python3
"""heatmaps.tf .vmf converter"""
import json
import sys
sys.path.insert(0, '../')
import vmf_tool

# Load Weapon IDs from Client Schema

def heatmap_vmf(heatmap, vmf='../mapsrc/blank.vmf', victims=True, killers=True, limit=None):
    """Takes a map name (e.g. cp_5days_a2) & creates a file from heatmaps.tf data"""
    try:
        base_vmf = vmf_tool.vmf_to_dict(open(vmf))
    except IOError:
        if '/' in vmf or '\\' in vmf:
            vmf = vmf.replace('\\', '/').rpartition('/')[-1]
        raise RuntimeError(f"Couldn't load {vmf} to inject props")

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

    class_names = {SCOUT: 'scout', SOLDIER: 'soldier', PYRO: 'pyro',
                   DEMOMAN: 'demo', HEAVY: 'heavy', ENGINEER: 'engineer',
                   MEDIC: 'medic', SNIPER: 'sniper', SPY: 'spy'}
    class_model = {k: f'models/player/{v}.mdl' for k, v in class_names.items()}

    # would hammer autofill missing values?
    prop_static = {'classname': 'prop_static',
                   'angles': '0 0 0', # bow to your partner. do-si-do
                   'fademindist': '-1', 'fadescale': '1',
                   'lightmapresolutionx': '32', 'lightmapresolutiony': '32',
                   'editor': {'color': '255 255 255', 'visgroupshown': '1',
                              'visgroupautoshown': '1',
                              'logicalpos': '[0 -1]'}} # what is logicalpos?

    props = []
    try: # could ent_id be used to count the limit?
        ent_id = max([e['id'] for e in base_vmf['entities']])
    except:
        ent_id = 0
        
    if limit is None: # 0 is a legal limit
        limit = heatmap['killcount']
    for kill in heatmap['kills']:
        victim = prop_static.copy()
        victim['id'] = ent_id
        ent_id += 1
        victim['model'] = class_model[kill[v_class]]
        victim['origin'] = f'{kill[v_x]} {kill[v_y]} {kill[v_z]}'
        victim['skin'] = '0' if kill[k_team] - 2 == 1 else '1'
        victim['editor']['comments'] = f'Killed by {class_names[kill[k_class]]} @ {kill[v_x]} {kill[v_y]} {kill[v_z]} with {kill[k_wep]}'
        # visgroup = victims
        if kill[k_class] == WORLD:
            victim['editor']['comments'] = f'Killed by WORLD'
            victim['angles'] = f'90 0 0'
            props.append(victim)
            continue
        props.append(victim)
        if ent_id >= limit:
            break
        
        killer = prop_static.copy()
        killer['id'] = ent_id
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
        killer['editor']['comments'] = f'Killed {class_names[kill[v_class]]} @ {kill[k_x]} {kill[k_y]} {kill[k_z]} with {kill[k_wep]}'
        # visgroup = killers
        props.append(killer)
        if ent_id >= limit:
            break

    base_vmf['entities'] = props
    return base_vmf

if __name__ == "__main__":
    import urllib.request
    # http://heatmaps.tf/api.html
    heatmap_site = 'http://heatmaps.tf/data/kills/'
    url_tail = '.json?fields=killer_class,killer_x,killer_y,killer_z,victim_class,victim_x,victim_y,victim_z,team,killer_weapon'
    # tell user which maps could not be heatmapped
    # heatmap.tf/data/maps.json only lists maps with valid overiews
    # heatmaps.tf API has rate limit of 20 requests per second per client
    import argparse
    # MUCH OF THIS IS NOT YET IMPLEMENTED
    # BUT IS PLANNED TO BE
    parser = argparse.ArgumentParser(description='Generate .vmf(s) from heatmaps.tf data', epilog="'@presets.txt' will load args from presets.txt", argument_default=[])
    # --verbose?
    parser.add_argument('-V', '--version', action='version', version='heatmap to vmf 1.0')
    CLASSES_DICT = ['WORLD', 'SCOUT', 'SOLDIER', 'PYRO', 'DEMO', 'HEAVY', 'ENGY', 'MEDIC', 'SNIPER', 'SPY']
    parser.add_argument('-filter-class', metavar='CLASS', action='append',
                        help='pairs with CLASS', choices=CLASSES)
    parser.add_argument('-filter-not-class', metavar='CLASS', action='append',
                        help='ignore pairs containing CLASS', choices=CLASSES)
    parser.add_argument('-filter-killer', metavar='CLASS', action='append',
                        help='killer_class must be CLASS', choices=CLASSES)
    parser.add_argument('-filter-victim', metavar='CLASS', action='append',
                        help='victim_class must be CLASS', choices=CLASSES)
                        # victim class cannot be WORLD
    parser.add_argument('-filter-weapon', metavar='WEAPON', action='append',
                        help='sampled from latest tf2 item schema')
    # -filter-custom-kill STATE
    # -filter-death-flag FLAG
    # instead of choices use: argparse.ArgumentError('WEAPON not found in client schema')
    # filter also weapon slots
    # some -filters will need additional fields in .json (modify url_tail)
    # use latest TF2 Client Item Schema (download or check vpk)
    parser.add_argument('-filter-range', metavar='RANGE', action='append', type=float,
                        help='pairs  >= RANGE units apart (inverted if negative)')
    # --filter-robot (names from mvm .pop files?)
    # would require -pop POPFILE
    parser.add_argument('--limit', type=int,
                        help='stop at LIMIT props (per map)')
    parser.add_argument('--out-folder', metavar='FOLDER', default='',
                        help='put generated .vmf(s) in this folder')
    hard_filters = parser.add_mutually_exclusive_group()
    hard_filters.add_argument('--only-killers', action='store_false', dest='killers',
                              help='list only killers')
    hard_filters.add_argument('--only-victims', action='store_false', dest='victims',
                              help='list only victims')
    parser.add_argument('--inject-vmf', metavar='VMF', # if not None: outfile = infile
                        help='inject ALL heatmaps into this .vmf')
    parser.add_argument('map', nargs='*', action='append', dest='maps', # raise ArgumentError if no map or folder
                       help="generate .vmf for each map's heatmap")
    parser.add_argument('-folder', metavar='FOLDER', action='append', dest='folders' # if not None: os.listdir() ...
                       help='generate .vmf for each map in FOLDER')

    # TEST ARGS
    parser.print_help() # PRINT PRETTIER
    args = parser.parse_args('koth_campania_a11 -filter-class SOLDIER -filter-class DEMO'.split())
    print(args)
    
    # for i, f in enumerate(folders):
    #     try:
    #         folders[i] = [x for x in os.listdir(f) if x.endswith('.vmf')]
    #     except:
    #        raise argparse.ArgumentError(f'{f} is not a valid folder')
    # args.maps = itertools.chain(args.maps, *folders)
    #
    # if args.out_folder is not None:
    #     if not os.isdir(args.out_folder):
    #         raise argparse.ArgumentError('OUT_FOLDER is not a folder!')
    #
    # create filter function for .json(s)
    # lambda k: all(any([k[field] == (a or b), ...]), ...)
    #
    # filter_weapons = any([??? for w in filter_weapons])
    
    def get_heatmap(filepath, filter=lambda k: True):
        """Foolproof heatmap generator"""
        filepath = filepath.replace('\\', '/')
        if '/' in filepath:
            outdir, sep, map_name = filepath.rpartition('/')
        else:
            map_name = filepath
            outdir = ''
        if map_name.endswith('.json'): # user downloaded .json
            heatmap = open(filepath) # may lack needed fields
        else: # file named same as map OR map name in terminal
            if '.' in map_name:
                map_name = map_name.rpartition('.')[0]
            heatmap = urllib.request.urlopen(f'{heatmap_site}/{map_name}{url_tail}')
        heatmap = heatmap_vmf(heatmap) # CONVERSION
        vmf_tool.export_vmf(heatmap, open(f'{outdir}/{map_name}_heatmap.vmf', 'w'))
