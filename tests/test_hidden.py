import os

from vmf_tool import Vmf


def node_is_a_brush(node) -> bool:
    if node.name == "hidden":
        node = node.nodes[0]
    if node.name == "solid":
        return True
    return False


def num_brushes_in_entity(node) -> int:
    if node.name == "hidden":
        node = node.nodes[0]
    if node.name == "entity":
        return sum(map(node_is_a_brush, node.nodes))
    return 0


def test_load_hidden():
    # load test vmf
    vmf_file = Vmf.from_file("tests/mapsrc/test_hidden_objects.vmf")

    # check all hidden objects loaded
    world_nodes = vmf_file._source.children("world")
    assert len(world_nodes) == 1
    worldspawn = world_nodes[0]

    worldspawn_node_is_brush = [
        node_is_a_brush(node)
        for node in worldspawn.nodes]
    num_world_brushes = worldspawn_node_is_brush.count(True)

    # NOTE: valvevmf would use:
    # -- assert num_world_brushes == len(worldspawn.children("solid"))
    # HOWEVER: this would miss any hidden brushes

    num_entity_brushes = sum([
        num_brushes_in_entity(node)
        for node in vmf_file._source.nodes])

    # NOTE: hard-coded numbers, do not edit test file!
    assert num_world_brushes == 14
    assert num_entity_brushes == 4
    total_brushes = num_world_brushes + num_entity_brushes  # 18
    assert len(vmf_file.hidden["brushes"]) == total_brushes
    assert len(vmf_file.brushes) == 18
    assert len(vmf_file.entities) == 4
    assert len(vmf_file.entity_brushes) == 2
    # TODO: assert func_detail & trigger_capture_area

    # is everything hidden?
    assert set(vmf_file.hidden["brushes"]) == set(vmf_file.brushes)
    assert set(vmf_file.hidden["entities"]) == set(vmf_file.entities)


def test_save_hidden():
    test2 = Vmf.from_file("tests/mapsrc/test2.vmf")

    # NOTE: this hiding system is a mess
    # hide a brush, an entity & a brush entity
    test2.hidden["brushes"].add(2)
    # ^ id of first brush
    test2.hidden["entities"].add(13)
    # ^ first entity (prop_dynamic: cap_point_base.mdl)
    test2.hidden["entities"].add(1652)
    # ^ first brush entity (func_detail: 8 brushes)

    # TODO: test hiding only some of a brush entity's brushes
    saved_filename = "tests/mapsrc/test2_hidden_copy.vmf"
    test2.save_as(saved_filename)

    # reload save to compare
    test2_resaved = Vmf.from_file(saved_filename)

    assert len(test2_resaved.hidden["brushes"]) == 1 + 8

    # NOTE: we delete the saved file only if all tests succeed
    # -- this way we can peek at the raw text; more info should help with debugging
    os.remove(test2_resaved.filename)
    vmx = test2_resaved.filename[:-1] + "x"
    if os.path.exists(vmx):
        os.remove(vmx)
