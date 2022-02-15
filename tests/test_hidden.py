import os

from vmf_tool import Vmf


def test_load_hidden():
    vmf_file = Vmf.from_file("tests/mapsrc/test_hidden_objects.vmf")
    # assert len(vmf_file.import_errors) == 0
    # check all hidden objects loaded
    world_node = {n.name: n for n in vmf_file._source.nodes}["world"]

    def node_is_a_brush(node):
        if node.name == "hidden":
            node = node.nodes[0]
        if node.name == "solid":
            return True
        return False

    def num_brushes_in_entity(node):
        if node.name == "hidden":
            node = node.nodes[0]
        if node.name == "entity":
            return sum(map(node_is_a_brush, node.nodes))
        return 0

    world_brushes_count = len([n for n in world_node.nodes if node_is_a_brush(n)])
    entity_brushes_count = sum(map(num_brushes_in_entity, vmf_file._source.nodes))
    # NOTE: exact numbers shouldn't matter if we trust the parser
    assert world_brushes_count == 14
    assert entity_brushes_count == 4
    assert len(vmf_file.hidden["brushes"]) == world_brushes_count + entity_brushes_count
    assert len(vmf_file.brushes) == 18
    assert len(vmf_file.entities) == 4
    assert len(vmf_file.brush_entities) == 2  # func_detail, trigger_capture_area
    # everything is hidden?
    assert set(vmf_file.hidden["brushes"]) == set(vmf_file.brushes)
    assert set(vmf_file.hidden["entities"]) == set(vmf_file.entities)


def test_save_hidden():
    test2 = Vmf.from_file("tests/mapsrc/test2.vmf")
    # hide a brush, an entity & a brush entity
    test2.hidden["brushes"].add(2)  # id of first brush
    test2.hidden["entities"].add(13)  # first entity (prop_dynamic: cap_point_base.mdl)
    test2.hidden["entities"].add(1652)  # first brush entity (func_detail: 8 brushes)
    # TODO: test hiding only some of a brush entity's brushes
    saved_filename = "tests/mapsrc/test2_hidden_resaved.vmf"
    test2.save_as(saved_filename)
    test2_resaved = Vmf.from_file(saved_filename)

    assert len(test2_resaved.hidden["brushes"]) == 1 + 8

    # NOTE: we delete the saved file only if all tests succeed
    # -- this way we can peek at the raw text; more info should help with debugging
    os.remove(test2_resaved.filename)
    vmx = test2_resaved.filename[:-1] + "x"
    if os.path.exists(vmx):
        os.remove(vmx)
