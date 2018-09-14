import copy
import sys
import vector
sys.path.insert(0, '../')
import vmf_tool

def check_materials(vmf, allowed_materials):
    if not hasattr(vmf.world, 'solids') and hasattr(vmf.world, 'solid'): # one world brush
        vmf.world.solids = [vmf.world.solid]
        del vmf.world.solid
    all_brushes = copy.deepcopy(vmf.world.solids)
    for entity in vmf.entities: # brush entities
        if hasattr(entity, 'solid'):
            if isinstance(entity.solid, vmf_tool.namespace):
                all_brushes.append(entity.solid)
        if hasattr(entity, 'solids'):
            if isinstance(entity.solids[0], vmf_tool.namespace):
                all_brushes += entity.solids
    for brush in all_brushes:
        for side in brush.sides:
            if side.material.upper() not in allowed_materials:
                face_triangle = [[float(i) for i in xyz.split()] for xyz in side.plane[1:-1].split(') (')]
                face_center = sum([vector.vec3(*v) for v in face_triangle], vector.vec3()) / 3
                yield f'Brush #{brush.id} Face @ {face_center:.2f} uses {side.material}'
                # View > Go To Brush Number... (Ctrl+Shift+G) in hammer
    

def check_props(vmf, allowed_props): # BUGGED?
    if not hasattr(vmf, 'entities') and hasattr(vmf, 'entity'): # one entity
        vmf.entities = [vmf.entity]
        del vmf.entity
    for entity in vmf.entities:
        if 'prop' in entity.classname:
            if entity.model.upper() not in allowed_props:
                short_propname = entity.model.lstrip('MODELS/')
                yield f'{entity.classname} @ {entity.origin} ({short_propname})'
                # View > Go To Coordinates... in hammer


if __name__ == "__main__":
    prop_list = open('2007_props.csv').read().split(',')
    material_list = open('2007_materials.csv').read().split(',') # should include tool textures
##    sys.argv.append('E:/Steam/SteamApps/common/sourcesdk_content/tf/mapsrc/sdk_cp_gravelpit.vmf')
    for vmf_file in sys.argv[1:]:
        print(f'Checking {vmf_file}...')
        vmf = vmf_tool.namespace_from(open(vmf_file))
        log = open(vmf_file[:-4] + '_asset_log.txt', 'w')
        print('### MATERIALS ###')
        log.write('### MATERIALS ###\n')
        for warning in check_materials(vmf, material_list):
            print(warning)
            log.write(warning + '\n')
        print('### PROPS ###')
        log.write('### PROPS ###\n')
        for warning in check_props(vmf, prop_list):
            print(warning)
            log.write(warning + '\n')
        log.close()
