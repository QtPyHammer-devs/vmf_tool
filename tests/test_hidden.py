import os

from vmf_tool import Vmf


def test_load_hidden():
    vmf_file = Vmf.from_file("tests/mapsrc/test_hidden_objects.vmf")
    # check all hidden objects loaded
    assert len(vmf_file.import_errors) == 0
    assert len(vmf_file.brushes) == 19  # BUG: hidden brushes attached to hidden entities not in brushes
    assert len(vmf_file.entities) == 4
    assert len(vmf_file.brush_entities) == 2  # func_detail, trigger_capture_area
    assert set(vmf_file.hidden["brushes"]) == set([b.id for b in vmf_file.brushes])
    assert set(vmf_file.hidden["entities"]) == set([e.id for e in vmf_file.entities])


def test_save_hidden():
    test2 = Vmf.from_file("tests/mapsrc/test2.vmf")
    # hide a brush, an entity & a brush entity
    test2.hidden["brushes"].add(2)  # id of first brush
    test2.hidden["entities"].add(13)  # first entity (prop_dynamic  cap_point_base.mdl)
    test2.hidden["entities"].add(1652)  # first brush entity (func_detail  8 brushes)
    # TODO: test hiding only some of a brush entity's brushes
    test2.save_as("tests/mapsrc/save_hidden_test.vmf")
    test2_resaved = Vmf.from_file("tests/mapsrc/save_hidden_test.vmf")

    assert len(test2_resaved.hidden["brushes"]) >= 2

    os.remove(test2_resaved.filename)  # delete saved file only if all tests succeed
    vmx = test2_resaved.filename[:-1] + "x"
    if os.path.exists(vmx):
        os.remove(vmx)
