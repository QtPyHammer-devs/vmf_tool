# vmf_tool
bare-bones python vmf importer for anylytics, visualisation &amp; editing

This project is focused on importing Valve's .vmf (Valve Map Format) files into python
The current goals / intended uses are:
  vmf debugging
  vmf visualisation
  entity I/O analysis and optimisation
  
Takes a very python specific approach: context specific code is written for every line of the .vmf as it's read
