import sys

import solid_tool
sys.path.append("../")
import vmf_tool


def vmf_to_obj(filename):
    """geometry only"""
    with open(filename) as file:
        vmf = vmf_tool.parse_lines(file.readlines())

    out_file = open(f"{filename}.obj", "w")
    out_file.write("# generated from" + filename + "\n")
    starting_v = 1
    for i, brush in enumerate(vmf.world.solids):
        buffer = [f"o solid_{i}"]
        solid = solid_tool.solid(brush)
        for v in solid.vertices:
            buffer.append(f"v {v.x} {v.y} {v.z}")
