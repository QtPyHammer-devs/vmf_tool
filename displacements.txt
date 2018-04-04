Source Displacement System

Per-vertex data for displacements is organised into rows
The number of rows and columns is dependent on the "power" of the displacement

Power 2 has 24: (2^Power + 1) ^ 2
Each row is split into 2^Power + 1 points
and this value is squared as displacements always have a 4 sided base

Each row contains sets of 3 floats, defining vectors
these vectors are assumed to be roughly equivalent to dispverts found in .bsp files
each dispvert is added to the barymetric coordinate at it's matching index

The order the barymetric coords are listed in is thus:
  0   1   2   3   4
  | \ | / | \ | / |
  5   6   7   8   9
  | / | \ | / | \ |
  10  11  12  13  14
  | \ | / | \ | / |
  15  16  17  18  19
  | / | \ | / | \ |
  20  21  22  23  24
I am very glad that dispverts are ordered in such a straightforward manner.

a 90 degree rotation (or some multiplication thereof) is quite straight forward.
  
bsp_tool.py already has a method for adding dispverts vectors
################################################################################
A = vector.vec3(*verts[0])
B = vector.vec3(*verts[1])
C = vector.vec3(*verts[2])
D = vector.vec3(*verts[3])
AD = D - A
BC = C - B
verts = []
power = dispinfo['power']
power2 = 2 ** power
start = dispinfo['DispVertStart']
stop = dispinfo['DispVertStart'] + (power2 + 1) ** 2
for index, dispvert in enumerate(self.DISP_VERTS[start:stop]):
    t1 = index % (power2 + 1) / power2
    t2 = index // (power2 + 1) / power2
    baryvert = vector.lerp(A + (AD * t1), B + (BC * t1), t2)
    dispvert = [x * dispvert['dist'] for x in dispvert['vec']]
    verts.append([a + b for a, b in zip(baryvert, dispvert)])
################################################################################

however the .bsp form of displacements have starting vertices;
A strange system connected to displacement stitching, to create triangle strips.
.bsp displacements also have a specific creation order,
uvs are mapped to barymetric coords before rotation & the addition of dispverts.
only this system requires each vertex's position must be calculated twice)

brushes in .vmf files are defined by a set of 3 points sorted clockwise & facing outwards for each side
however the starting point is defined by a "startposition" key in the side's dispinfo

dispverts come in two parts, vector and length, ?this is an attempt to preserve floating point accuracy?
each dispvert is created by multiplying vector by distance

testing will be required to see what exactly occurs when a instances containting disp are collapsed
presumably rotations are and poistional offsets are not applied to collapsed disps while compiling
ideally a command line script called before the vbsp.exe stage of compiling can fix any errors
