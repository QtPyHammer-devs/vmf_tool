"""Schema Spelunking Kit"""
import sys
sys.path.insert(0, '../')
import vmf_tool
print('schema_dict = dict ... ', end='')
schema_dict = vmf_tool.dict_from(open('tf2_client_schema'))
print('Done!')
print('schema = namespace ... ', end='')
schema = vmf_tool.namespace_from(schema_dict)
print('Done!')
# schema.items_game.items[813].name = "The Neon Annihilator"
print('ids = {name: id, ...} ... ', end='')
ids = {k: v for k, v in schema.items_game.items.items() if str.isdigit(k)}
print('Done!')

# weapon / item ids to file
##outfile = open('item_ids', 'w')
##for line in vmf_tool.lines_from({'ids': ids}):
##    outfile.write(line)

# contract type names
##for v in schema2.items_game.kill_eater_score_types.values():
##	print(v.type_name.partition('_')[2])

# filter weapons by prefab craft_type slot

# WANT TO MATCH SETS OF NUMBERS TO WEAPONS / SLOTS / PREFABS

prefabs = {}
for code, item in ids.items():
    if hasattr(item, 'prefab'):
        item_prefabs = item.prefab.split()
        s = '\n\t'.join(item_prefabs)
##        print(f"{code}: {item.name}\n\t{s}")
        for prefab in item_prefabs:
            if prefab not in prefabs.keys():
                prefabs[prefab] = [code]
            else:
                prefabs[prefab].append(code)

prefab_dict = schema.items_game.prefabs

# item names for specific prefab
##for p in prefabs['valve']:
##	print(f'{p}: {ids[p].name}')

for w_p in [p for p in prefabs if p.startswith('weapon_')]:
    print(w_p)
    for w in prefabs[w_p]:
        print(f'\t{w}: {ids[w].name}')

ids2 = vmf_tool.namespace_from(ids)

# WHERE IS TIDE TURNER?
# WEAPONS BY CLASS?
# CHECK ASD417 KILL ON COS_MANSION_A2

for p, x in prefab_dict.items():
    if p.startswith('weapon_'):
        if 'demoman' in getattr(x, 'used_by_classes', dict()):
            print(p)
