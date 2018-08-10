"""Moves displacements to identically shaped faces with the material 'DEV/DEV_BLENDMEASURE'"""
import sys
sys.path.insert(0, '../')
import vmf_tool

##sys.argv.append('../mapsrc/dispcopy.vmf') # TEST
for file in sys.argv[1:]:
    print(f'Loading {file}...')
    vmf = vmf_tool.namespace_from(open(file))

    new_disps = set()
    old_disps = set()
    disp_sides = dict() # {plane: side}
    print('Tagging Faces')
    for i, solid in enumerate(vmf.world.solids):
        for side in solid.sides:
            if hasattr(side, 'dispinfo'):
                disp_sides[side.plane] = side
                old_disps.add(i)
            if side.material == "DEV/DEV_BLENDMEASURE":
                new_disps.add(i)

    print('Copying Displacements')
    for i in new_disps:
        solid = vmf.world.solids[i]
        for j, side in enumerate(solid.sides):
            if side.plane in disp_sides:
                vmf.world.solids[i].sides[j] = disp_sides[side.plane]

    vmf.world.solids = [s for i, s in enumerate(vmf.world.solids) if i not in old_disps]

    print('Writing...')
    new_vmf = open(f'{file}_clean.vmf', 'w')
    buffer = ''
    for line in vmf_tool.lines_from(vmf):
        buffer += line
        if len(buffer) > 100:
            new_vmf.write(buffer)
            buffer = ''
    new_vmf.write(buffer)
    new_vmf.close()
    print('Conversion Done!')
