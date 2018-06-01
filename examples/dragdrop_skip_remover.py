import sys
sys.path.insert(0, '../')
import vmf_tool

brush_func = lambda solid: not all([side['material'] == 'TOOLS/TOOLSSKIP' for side in solid['sides']])

for filepath in sys.argv[1:]:
    vmf = vmf_tool.vmf(open(filepath))
    vmf.dict['world']['solids'] = [*filter(brush_func, vmf.dict['world']['solids'])]
    vmf.export(open(f'{filepath[:-4]}_skipless.vmf', 'w'))
input('Press Enter to Quit')
    
