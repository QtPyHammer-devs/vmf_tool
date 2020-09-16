# vmf_tool
A library for interpreting & editing .vmf files

This library was created for editing Valve's .vmf (Valve Map Format)  
Created as part of [QtPyHammer](https://github.com/snake-biscuits/QtPyHammer)  

The core parser is very lazy, anything that looks like a .vmf will be parsed  
Once parsed, any issues with the source file can be traced to a rough line number  
Ideally allowing for the recovery of corrupted .vmfs  
