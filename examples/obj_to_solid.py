import itertools
import vector

def obj_solid(filepath):
    """turns faces into sides of a .vmf solid"""
    solid = {"id": "0", "sides": [], "editor": {
                 "color": "255 0 255", "visgroupshown": "1",
                 "visgroupautoshown": "1"}}
    file = open(filepath)
    v  = []
    side_id = 0
    for line in file.readlines():
        line = line.rstrip('\n')
        if line.startswith('v'):
            v.append([float(f) for f in line.split(' ')[1:]])
        elif line.startswith('f'):
            line = line.replace('\\', '/').split(' ')[1:]
            plane = [] # () () ()
            for point in line[:3]:
                vertex = v[int(point.split('/')[0]) - 1]
                plane.append(' '.join([str(x) for x in vertex]))
            plane = reversed(plane)
            side_id += 1
            solid['sides'].append({
                'id': side_id,
                'plane': '(' + ') ('.join(plane) + ')',
                'material': 'TOOLS/TOOLSNODRAW',
                'uaxis': '[0 -1 0 0] 0.25',
		'vaxis': '[0 0 -1 0] 0.25',
		'rotation': '0',
		'lightmapscale': '16',
		'smoothing_groups': '0'})
    file.close()
    return solid

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '../')
    import vmf_tool
    base = vmf_tool.vmf(open('../mapsrc/blank.vmf'))
    for filepath in sys.argv[1:]:
        ...
        # outfile = open(f'{filepath[:-4]}.vmf', 'w')
    hemisphere = obj_solid('hemisphere.obj')
    base.dict['world']['solid'] = hemisphere
    base.export(open('hemisphere.vmf', 'w'))
