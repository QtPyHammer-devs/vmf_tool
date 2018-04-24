# vmf_tool
bare-bones python vmf importer for anylytics, visualisation &amp; editing

This project is focused on importing Valve's .vmf (Valve Map Format) files into python

Current intended uses are:
  + vmf debugging
  + vmf visualisation
  + entity I/O analysis and optimisation
  
Takes a very python specific approach: context specific code is written for every line of the .vmf as it's read

Planned Features
 - [x] export back to vmf
 - [ ] displacement vector rotation (for instance collaspsing, unless VMFII already handles this)
 - [x] solid planes to full faces (almost!)
 - [ ] invalid solid recovery (what defines an invalid solid? inward facing planes?)
 - [ ] 2-way obj conversion
