import sys
sys.path.insert(0, '../')
import vmf_tool

brush_func = lambda solid: not all([side['material'] == 'TOOLS/TOOLSSKIP' for side in solid['sides']])

for filepath in sys.argv[1:]:
    file = vmf_tool.vmf_to_dict(open(filepath))
    file['world']['solids'] = [*filter(brush_func, file['world']['solids'])]
    vmf_tool.export_vmf(file, open(f'{filepath[:-4]}_skipless.vmf', 'w'))
input('Press Enter to Quit')
    
