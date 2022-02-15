# vmf_tool
A library for interpreting & editing .vmf files

This library was created for editing Valve's .vmf (Valve Map Format)
Parsing is provided by [ValveVmf](https://github.com/QtPyHammer-devs/ValveVMF)

Created as part of [QtPyHammer](https://github.com/QtPyHammer-devs/QtPyHammer)

## Installation
To use the latest version, clone from git & install dependencies:
```
$ git clone git@github.com:QtPyHammer-devs/vmf_tool.git
$ python -m pip install -r requirements.txt
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
