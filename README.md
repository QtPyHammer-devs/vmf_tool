# vmf_tool
A library for interpreting & editing .vmf files

This library was created for editing Valve's .vmf (Valve Map Format)  
Created as part of [QtPyHammer](https://github.com/snake-biscuits/QtPyHammer)  

## Installation
To use the latest version, clone from git:
```
$ git clone git@github.com:QtPyHammer-devs/vmf_tool.git
```

Or to use the latest stable release, install via [pip](https://pypi.org/project/vmf-tool/) (Python 3.7+):
```
pip install vmf_tool
```

## Usage
```python
>>> import vmf_tool
>>> some_map = vmf_tool.Vmf.from_file("mapsrc/some_map.vmf")
>>> some_map.save_as("mapsrc/some_map.vmf.copy")
```
<!--
>>> mins = (-256,) * 3
>>> maxs = (256,) * 3
>>> some_map.brushes.append(vmf_tool.Brush.from_bounds(mins, maxs))
>>> some_map.save()
```
-->
