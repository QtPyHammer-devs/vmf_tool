import os

import vmf_tool


def test_load_from_file():
    test2 = vmf_tool.Vmf.from_file("tests/mapsrc/test2.vmf")
    assert len(test2.import_errors) == 0
    # do empty .vmfs raise errors?
    blank = vmf_tool.Vmf.from_file("tests/mapsrc/blank.vmf")
    assert len(blank.import_errors) == 0
    # TODO: test parser correctly handles:
    # only one brush
    new_brush = vmf_tool.solid.Brush.from_bounds((-64, -64, -64), (64, 64, 64))
    new_brush.id = 1
    blank.brushes[1] = new_brush
    # TODO: save, reload, assert
    # only one entity
    # only one brush inside an entity


def test_save_quality():
    original_filename = "tests/mapsrc/test2.vmf"
    saved_filename = "tests/mapsrc/save_test.vmf"
    vmf_tool.Vmf.from_file(original_filename).save_as(saved_filename)

    original_vmf = vmf_tool.Vmf.from_file(original_filename)
    saved_vmf = vmf_tool.Vmf.from_file(saved_filename)

    assert len(saved_vmf.import_errors) == len(original_vmf.import_errors)
    assert len(saved_vmf.brushes) == len(original_vmf.brushes)
    for saved_brush, original_brush in zip(saved_vmf.brushes, original_vmf.brushes):
        for saved_face, original_face in zip(saved_brush, original_brush):
            # TODO: determine a margin of error for comparing brushes
            assert saved_face.plane == original_face.plane
    assert len(saved_vmf.entities) == len(original_vmf.entities)
    os.remove(saved_filename)  # delete saved file only if all tests succeed
    saved_filename_vmx = saved_filename[:-1] + "x"
    if os.path.exists(saved_filename_vmx):
        os.remove(saved_filename_vmx)


def test_blank_save():
    original_filename = "tests/mapsrc/blank.vmf"
    saved_filename = "tests/mapsrc/blank_save_test.vmf"
    vmf_tool.Vmf.from_file(original_filename).save_as(saved_filename)

    original_vmf = vmf_tool.Vmf.from_file(original_filename)
    saved_vmf = vmf_tool.Vmf.from_file(saved_filename)

    assert len(saved_vmf.import_errors) == len(original_vmf.import_errors)
    assert len(saved_vmf.brushes) == len(original_vmf.brushes)
    assert len(saved_vmf.entities) == len(original_vmf.entities)
    os.remove(saved_filename)  # delete saved file only if all tests succeed
    saved_filename_vmx = saved_filename[:-1] + "x"
    if os.path.exists(saved_filename_vmx):
        os.remove(saved_filename_vmx)


def test_connections():  # ISSUE #13  (Unwanted removal of duplicate keys...)
    test2_vmf = vmf_tool.Vmf.from_file("tests/mapsrc/test2.vmf")
    cp1 = [e for e in test2_vmf.entities.values() if getattr(e, "targetname", None) == "cp1"][0]
    # ^ need a more convenient way of accessing entities by name
    assert len(cp1.connections.OnCapTeam1) == 2
    assert len(cp1.connections.OnCapTeam2) == 2
