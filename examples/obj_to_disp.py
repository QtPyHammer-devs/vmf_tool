## TODO: split concave solids at most concave points
## TODO: efficient use of solids (as many sides as possible)
## TODO: decent auto-generated texture-vecs (match to obj?)
import vector

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
    for line in file.readlines:
        line = line[:-1] #remove \n
        if line.startswith('v'):
            v.append([float(f) for f in line.split(' ')[1:]])
        elif line.startswith('f'):
            # if quads, triangulate
            for point in line.split(' ')[1:]:
                vertex = v[int(point.split('/')[0]) - 1]
                if vertex not in vertices:
                    vertices.append(vector.vec3(*vertex))
                    indices.append(vertex_count)
                    vertex_count += 1
                else:
                    indices.append(vertices.index(full_vert))
    file.close()
    return vertices, indices


# segments greater than 81 (power 3) must be split
def points_to_disp(vertices, indices):
    # find average plane (axis & grid align if possible)
    # find corners of this plane
    # corners will have least nodes (4 which appear only once in indices)
    # the next (2**pow - 1) * 4 will be edges (touch 2 times)
    ### this only applies to split displacements
    ### map neighbours?
    neighbourhood = {[x]: set() for x in range(len(vertices))}
    # remember! sets cannot be indexed!
    # however, they can be iterated over!
    for i, index in enumerate(indices[::3]):
        i *= 3
        tri = [index, indices[i + 1], indices[i + 2]]
        for j, v in enumerate(tri):
            neighbourhood[v].add(tri[:j - 1])
            neighbourhood[v].add(tri[j:])
    # DON'T SORT CLOCKWISE
    # SORT ALONG EDGES
    # |0 \ 1 / 2 \ 3 / 4|
    # |  -   - | -   -  |
    # |5 / 6 \ 7 / 8 \ 9| 
    # generate base solid
    # create barymetric space
    # generate disp-vec for nearest point to each barymetric point
    # assign each vertex a position on a row in the A -> B direction
    # generate vmf solid
    ### MAIN PATTERN
    #ROW 0 = |\|/| * POWER
    #ROW 1 = |/|\| * POWER
    # repeat POWER times
    if vertex_count == 25: # you're my power 2
        ... # and i get my kicks just out of you
        # match to barymetrics
        # calculate vectors & scales
    elif vertex_count == 81:
        ...
    elif ...:
        ...
    
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
