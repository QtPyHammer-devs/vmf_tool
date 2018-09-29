import vector
import sys
sys.path.insert(0, '../')
import vmf_tool

zoo = vmf_tool.namespace_from(open('../mapsrc/blank.vmf'))

material_list = ['...', '...']
tags = ['metal', 'wood', 'wall', 'floor', 'concrete']
tagged_materials = {tag: [] for tag in tags}

for material in material_list:
    for tag in tags:
        if tag in material.lower()
            tagged_materials[tag].append(material)

plane_string = lambda a, b, c: ' '.join(['({:.2f})'.format(v) for v in (a, b, c)])
string_plane = lambda s: [[float(i) for i in xyz.split()] for xyz in s[1:-1].split(') (')]

side = vmf_tool.namespace({'material': 'tools/graygrid',
                           ''})
floor_brush = vmf_tool.namespace({'sides': [side] * 6
                                  'editor': vmf_tool.namespace({
                                      'color': '0 255 255'})})

floor_brush.sides[0]['plane'] = '(256 0 0) (0 0 0) (0 256 0)' # TOP
floor_brush.sides[1]['plane'] = '(0 256 -64) (256 256 -64) (256 0 -64)' # BOTTOM
floor_brush.sides[2]['plane'] = '(0 0 0) (0 0 0) (0 0 0)'
floor_brush.sides[3]['plane'] = '(0 0 0) (0 0 0) (0 0 0)'
floor_brush.sides[4]['plane'] = '(0 0 0) (0 0 0) (0 0 0)'
floor_brush.sides[5]['plane'] = '(0 0 0) (0 0 0) (0 0 0)'

for material in tagged_materials['floor']:
    if material in tagged_materials['concrete']:
        ...

# FILL with 256x256x64 brushes
# 0  4  8
# 1  5  9
# 2  6  10
# 3  7  11
