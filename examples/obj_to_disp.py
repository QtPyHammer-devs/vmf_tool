## TODO: split concave solids at most concave points
## TODO: efficient use of solids (as many sides as possible)
## TODO: decent auto-generated texture-vecs (match to obj?)
## TODO: port test .objs into modified mapsrc/blank.vmf
import itertools
import vector

# remember default .obj orientation is +Y-UP -Z-FORWARD
# orientation is not specified in the file
# assuming +Z-UP +Y-FOWARD for now
def get_obj_vertices(filepath):
    """position data only"""
    file = open(filepath)
    # predefined splitting (to match bsp to obj style)
    # g = [object, ...]
    # o = [[vertex, ...], [index, ...]]
    # each object is a displacement
    # each group is a solid (bsp just makes all disps the same group)
    v  = []
    vertex_count = 0
    vertices = []
    indices = []
    for line in file.readlines():
        line = line[:-1] # remove \n
        if line.startswith('v'):
            v.append([float(f) for f in line.split(' ')[1:]])
        elif line.startswith('f'):
            line = line.split(' ')[1:]
            if len(line) == 4: #QUADS ONLY! for neighbour map
                for point in line:
                    vertex = v[int(point.split('/')[0]) - 1]
                    vertex = vector.vec3(*vertex)
                    if vertex not in vertices:
                        vertices.append(vertex)
                        indices.append(vertex_count)
                        vertex_count += 1
                    else:
                        indices.append(vertices.index(vertex))
    file.close()
    return vertices, indices

# segments greater than 81 (power 3) must be broken down
def points_to_disp(vertices, indices): # THIS METHOD IS FOR QUADS ONLY!
    """expects quads the size of a power2 or 3 displacement"""
    neighbourhood = {x: set() for x in range(len(vertices))}
    # not working as it should
    for i, index in enumerate(indices[::4]):
        i *= 4
        quad = [index, indices[i + 1], indices[i + 2], indices[i + 3]]
        for i, point in enumerate(quad):
            neighbourhood[point].add(quad[i - 1])
            neighbourhood[point].add(quad[i + 1 if i != 3 else 0])
    # use neighbourhood map to split at poles? (5 + neighbours)
    # DON'T SORT CLOCKWISE
    # SORT ALONG EDGES
    # |0 \ 1 / 2 \ 3 / 4|
    # |5 / 6 \ 7 / 8 \ 9|
    corners = [*filter(lambda i: len(neighbourhood[i]) == 2, neighbourhood)]
    edges = [*filter(lambda i: len(neighbourhood[i]) == 3, neighbourhood)]
    edges = [*itertools.chain(corners[1:], edges)]
    print(neighbourhood)
    print(corners)
    print(edges)
    # A must touch B & D, but never C
    # B must touch A & C, but never D
    # C must touch B & D, but never A
    # D must touch A & C, but never B

    # this sequencer needs to be a function
    # should recycle this for rows
    A = corners[0]
    AB = [A, list(neighbourhood[A])[0]] 
    while not any([c in AB for c in corners[1:]]):
        next_edge = neighbourhood[AB[-1]]
        next_edge = [*filter(lambda x: x not in AB and x in edges, next_edge)]
        AB += next_edge
    B = AB[-1]
    print(AB)

    
    BC = [B] # and B's neighbour that isn't in AB
    # split edges into neighbour sequences
    # match edges to corners
    
    # generate base solid
    # create barymetric space from corners
    # generate disp-vec matching points to barymetric coords (preserve neighbours)
    # generate vmf solid
    ### CORE PATTERN
    #ROW 0 = |\|/| * POWER
    #ROW 1 = |/|\| * POWER
    # repeat POWER times

# sample displacement face    
##side
##{
##        "id" "1"
##        "plane" "(-256 256 0) (256 256 0) (256 -256 0)" // +Z-UP
##        "material" "DEV/DEV_BLENDMEASURE" // orange-grey grid
##        "uaxis" "[1 0 0 0] 0.25"
##        "vaxis" "[0 -1 0 0] 0.25"
##        "rotation" "0"
##        "lightmapscale" "16"
##        "smoothing_groups" "0"
##        // ^^ the usual ^^
##        dispinfo
##        {
##                "power" "2"
##                "startposition" "[-256 -256 0]" // corner A
##                "flags" "0"
##                "elevation" "0"
##                "subdiv" "0"
##                normals
##                {
##                        // each 3 define a normalised vector
##                        "row0" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                        "row1" "0 0 0 0 0 1 0 0 0 0 0 1 0 0 0"
##                        "row2" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                        "row3" "0 0 0 0 0 1 0 0 0 0 0 1 0 0 0"
##                        "row4" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                }
##                distances
##                {
##                        // scales to match vectors from earlier
##                        "row0" "0 0 0 0 0"
##                        "row1" "0 32 0 32 0"
##                        "row2" "0 0 0 0 0"
##                        "row3" "0 32 0 32 0"
##                        "row4" "0 0 0 0 0"
##                }
##                offsets
##                {
##                        // ???
##                        "row0" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                        "row1" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                        "row2" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                        "row3" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                        "row4" "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
##                }
##                offset_normals
##                {
##                        // ???
##                        "row0" "0 0 1 0 0 1 0 0 1 0 0 1 0 0 1"
##                        "row1" "0 0 1 0 0 1 0 0 1 0 0 1 0 0 1"
##                        "row2" "0 0 1 0 0 1 0 0 1 0 0 1 0 0 1"
##                        "row3" "0 0 1 0 0 1 0 0 1 0 0 1 0 0 1"
##                        "row4" "0 0 1 0 0 1 0 0 1 0 0 1 0 0 1"
##                }
##                alphas
##                {
##                        // per-vertex texture blend (0 - 255)
##                        "row0" "0 0 0 0 0"
##                        "row1" "0 255 0 255 0"
##                        "row2" "0 0 0 0 0"
##                        "row3" "0 255 0 255 0"
##                        "row4" "0 0 0 0 0"
##                }
##                triangle_tags
##                {
##                        // physics / walkable? (see bsp docs)
##                        "row0" "9 9 9 9 9 9 9 9"
##                        "row1" "9 9 9 9 9 9 9 9"
##                        "row2" "9 9 9 9 9 9 9 9"
##                        "row3" "9 9 9 9 9 9 9 9"
##                }
##                allowed_verts
##                {
##                        // 10 * -1 is default (???)
##                        "10" "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1"
##                }


if __name__ == "__main__":
    import sys
    for filepath in sys.argv[1:]:
        #convert objs into displacements, creating files for each
        ...

    vertices, indices = get_obj_vertices('power2_disp_quads.obj')
    points_to_disp(vertices, indices)
