## TODO: split concave solids at most concave points
## TODO: efficient use of solids (as many sides as possible)
## TODO: decent auto-generated texture-vecs (match to obj?)
## TODO: port test .objs into modified mapsrc/blank.vmf
## TODO: move towards group-object oriented system
# multi-res scultping may result in strange poles and create issues
# need to keep displacement form but map creases (without warping uvs too much)
import itertools
import vector

# remember default .obj orientation is +Y-UP -Z-FORWARD
# orientation is not specified in the file
# assuming +Z-UP +Y-FOWARD for now
def get_obj_vertices(filepath):
    """positions only"""
    file = open(filepath)
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

def obj_out(filepath):
    """positions & groupings only"""
    file = open(filepath)
    g = ['group0'] # (name, object_name1, ...)
    groups = []
    o = ['object0', 0, 0] # (name, start, end)
    objects = {} #{name: (start, end)}
    v = []
    vertices = []
    indices = []
    for line in file.readlines():
        line = line[:-1]
        if line.startswith('g'):
            groups.append(g)
            g = [' '.join(line.split()[1:])]
        elif line.startwith('o'):
            objects[o[0]] = o[1:]
            o = [' '.join(line.split()[1:]), o[2] + 1, 0]
            g.append(o[0])
        elif line.startswith('v'):
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
                    o[2] += 1
    return vertices, indices, objects, groups


def get_street(start, neighbourhood, n_filter=lambda x: True): # for edges
        """a street is a sequence of neighbours\nneighbourhood map must index points"""
        out = start # expecting the first two neighbours of the street
        good_neighbour = lambda x: x not in out and n_filter(x)
        while True:
            neighbours = neighbourhood[out[-1]]
            next_neighbour = [*filter(good_neighbour, neighbours)]
            if len(next_neighbour) == 1:
                out += next_neighbour
            else:
                break
        return out


def get_paralell_street(start, adjacent_street, neighbourhood): # no user filter
    """a street is a sequence of neighbours\nneighbourhood map must index points"""
    out = start
    for other_neighbour in adjacent_street[1:]:
        good_neighbour = lambda x: x in neighbourhood[other_neighbour] and x not in adjacent_street
        neighbours = neighbourhood[out[-1]]
        next_neighbour = [*filter(good_neighbour, neighbours)]
        out.append(next_neighbour[0])
    return out


def quads_to_rows(vertices, indices):
    neighbourhood = {x: set() for x in range(len(vertices))} #a map that tells you who your neighbours are
    for i, index in enumerate(indices[::4]):
        i *= 4
        quad = [index, indices[i + 1], indices[i + 2], indices[i + 3]]
        for i, point in enumerate(quad):
            neighbourhood[point].add(quad[i - 1])
            neighbourhood[point].add(quad[i + 1 if i != 3 else 0])
    corners = [*filter(lambda i: len(neighbourhood[i]) == 2, neighbourhood)]
    edges = [*filter(lambda i: len(neighbourhood[i]) == 3, neighbourhood)]

    is_edge = lambda point: point in edges
    end_corner = lambda street: [*filter(lambda neighbour: neighbour in corners, neighbourhood[street[-1]])][0]

    A = corners[0]
    A_edge_neighbours = [*filter(is_edge, neighbourhood[A])]
    AB = get_street([A, A_edge_neighbours[0]], neighbourhood, n_filter=is_edge)
    B = end_corner(AB)
    AB.append(B)

    AD = get_street([A, A_edge_neighbours[1]], neighbourhood, n_filter=is_edge)
    D = end_corner(AD)
    AD.append(D)

    rows = [AB]
    for start in AD[1:]:
        # good neighbour is neighbour of rows[-1][i + 1]
        row = get_paralell_street([start], rows[-1], neighbourhood)
        rows.append(row)
    return rows
    
# generate a solid in a sensible place and turn it into displacements

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '../')
    import vmf_tool
    # base = vmf(open('../mapsrc/blank.vmf'))
    for filepath in sys.argv[1:]:
        ## convert objs into displacements, creating files for each
        # out_vmf = base
        # outfile = open(f'{filepath[:-4]}.vmf', 'w')
        ## generate solids, and inject into vmf
        ...

    ### INJECTS DISPLACEMENT DATA INTO A DISPLACEMENT MADE IN HAMMER ###
    vertices, indices = get_obj_vertices('power2_disp_quads.obj')
    rows = quads_to_rows(vertices, indices)
    # make rows relative to barymetric coords
    # indices > vertices > vectors
    A = vector.vec3(*vertices[rows[0][0]])
    B = vector.vec3(*vertices[rows[0][-1]])
    C = vector.vec3(*vertices[rows[-1][-1]])
    D = vector.vec3(*vertices[rows[-1][0]])
    AD = D - A
    BC = C - B
    vector_rows = []
    # rows are nice and easy to split!
    # use vector.lerp for boundaries between disps of different powers
    for x, row in enumerate(rows): # assuming power 2
        x = x / 4
        vector_rows.append([])
        for y, index in enumerate(row):
            y = y / 4
            bary_point = vector.lerp(A + (AD * x), B + (BC * x), y)
            point = vertices[index] - bary_point
            vector_rows[-1].append(point)
           
    base_vmf = vmf_tool.vmf(open('../mapsrc/test_disp.vmf'))
    dispinfo = vmf_tool.scope(['world', 'solid', 'sides', 0, 'dispinfo']) # solid 0, side 0
    exec(f"base_vmf.dict{dispinfo}['startposition'] = '[{A.x} {A.y} {A.z}]'")
    for i, row in enumerate(vector_rows):
        row_distances = [v.magnitude() for v in row] # 1 per vert
        row_normals = [v / w if w != 0 else vector.vec3() for v, w in zip(row, row_distances)] # 3 per vert
        row_normals = [*map(lambda v: f'{v}', row_normals)]
        row_distances = [*map(str, row_distances)]
        exec(f"base_vmf.dict{dispinfo}['distances']['row{i}'] = ' '.join(row_distances)")
        exec(f"base_vmf.dict{dispinfo}['normals']['row{i}'] = ' '.join(row_normals)")

    base_vmf.export(open('power2_obj.vmf', 'w'))
