import sys
sys.path.insert(0, '../')
import vmf_tool

#sadly not 100% accurate to compiled values
#also incredibly buggy
for file in sys.argv[1:]:
    vmf_file = vmf_tool.vmf(open(file))
    print('***', vmf_file.filename.split('\\')[-1])
    brushes = 0
    brushsides = 0
    for solid in vmf_file.dict['world']['solids']:
        brushes += 1
        brushsides += len(solid['sides'])
    for entity in vmf_file.dict['entities']:
        #finicky and likely unreliable
        if 'solids' in entity.keys():
            for solid in entity['solids']:
                brushes += 1
                brushsides += len(solid['sides'])

    fullness = brushes / 8192
    print(f'{brushes}/8192 brushes ({fullness * 100:.1f}%)', end=' ')
    if fullness > 1:
        if brushes == 8193:
            print('one brush too many')
        else:
            print(f'{brushes - 8192} too many brushes')
    else:
        print()

    fullness = brushsides / 65536
    print(f'{brushsides}/65535 brushsides ({fullness * 100:.1f}%)', end=' ')
    if fullness <= .7:
        print('well within acceptable paramaters')
    elif .7 < fullness <= .8:
        print('quite full actually')
    elif .8 < fullness <= .9:
        print('extremely full')
    elif .9 < fullness < 1:
        print('nearly full')
    elif fullness == 1:
        print('just right') #sadly many terminals do not support emoji
                            #if they did I know what I'd put here
    elif 1 < fullness <= 1.25:
        print('woah there')
    elif 1.25 < fullness <= 1.5:
        print("let's not get carried away")
    elif 1.5 < fullness <= 1.75:
        print("this isn't funny")
    elif 1.75 < fullness <= 2:
        print("have you considered creating a multi-map project?")
    elif fullness == 2:
        print('>>> METAL GEAR RISING: REVENGANCE JOKE <<<')
    else:
        print('\n', 'this is fine.' * 80, sep='')
    if fullness > 1:
        print(f'{brushsides - 65536} brushes too many')
input('Press Enter to exit')
