def obj_solids(filepath): # split by object and group
    """turns faces into sides of a .vmf solid"""
    file = open(filepath)
    v  = []
    side_id = 0
    brush = {"sides": [], "editor": {
                 "color": "255 0 255", "visgroupshown": "1",
                 "visgroupautoshown": "1"}}
    brush_id = 0
    solids = []
    solids.append(brush.copy())
    solids[-1]['id'] = brush_id
    brush_id += 1
    for line in file.readlines():
        line = line.rstrip('\n')
        if line.startswith('v'):
            v.append([float(f) for f in line.split(' ')[1:]])
        elif line.startswith('f'):
            line = line.replace('\\', '/').split(' ')[1:]
            plane = []
            for point in line[:3]:
                vertex = v[int(point.split('/')[0]) - 1]
                plane.append(' '.join([str(x) for x in vertex]))
            plane = reversed(plane)
            side_id += 1
            solids[-1]['sides'].append({
                'id': side_id,
                'plane': '(' + ') ('.join(plane) + ')',
                'material': 'TOOLS/TOOLSNODRAW',
                'uaxis': '[0 -1 0 0] 0.25',
		'vaxis': '[0 0 -1 0] 0.25',
		'rotation': '0',
		'lightmapscale': '16',
		'smoothing_groups': '0'})
        elif line.startswith('o'):
            solids.append(brush.copy())
            solids[-1]['id'] = brush_id
            brush_id += 1
    if len(solids[0]['sides']) == 0:
        solids = solids[1:]
    file.close()
    return solids

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '../')
    import vmf_tool
    with open('../mapsrc/blank.vmf') as base_file:
        base = vmf_tool.parse_lines(base_file.readlines())
    for filepath in sys.argv[1:]:
        base.dict['world']['solids'] = obj_solids(filepath)
        with open(f'{filepath}.vmf', 'w') as out_file:
            export(base, out_file)

    ##TEST    
    # hemisphere = obj_solids('hemisphere.obj')
    # base.dict['world']['solids'] = hemisphere
    # base.export(open('hemisphere.vmf', 'w'))
