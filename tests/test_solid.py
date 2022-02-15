from vmf_tool import vector
from vmf_tool import solid


def test_plane_of():
    A = (0, 0)
    B = (0, 1)
    C = (1, 1)
    Z_up = vector.vec3(z=1)
    assert solid.plane_of(vector.vec3(*A), vector.vec3(*B), vector.vec3(*C)) == (Z_up, 0.0)
    assert solid.plane_of(vector.vec3(*A, 2), vector.vec3(*B, 2), vector.vec3(*C, 2)) == (Z_up, 2.0)
