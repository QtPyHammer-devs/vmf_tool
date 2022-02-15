import os

import pytest

import vmf_tool


# TODO: test handling of malformed .vmfs
# -- 0 bytes files, incomplete files, invalid keyvalues etc.

def test_load_from_file():
    """Will it crash?"""
    # TODO: give a (X / max) success rate in final result
    # TODO: re-implement import_errors to allow for partial loads
    # -- scrapping invalid brushes etc. like regular hammer
    blank = vmf_tool.Vmf.from_file("tests/mapsrc/blank.vmf")  # nothing
    # assert len(blank.import_errors) == 0
    test = vmf_tool.Vmf.from_file("tests/mapsrc/test.vmf")  # nodraw cube
    # assert len(test.import_errors) == 0
    test2 = vmf_tool.Vmf.from_file("tests/mapsrc/test2.vmf")  # various objects
    # assert len(test2.import_errors) == 0
    # NOTE: test save hidden
    del blank, test, test2


@pytest.mark.parametrize("filename", ("blank", "test", "test2"))
def test_save_quality(filename):
    map_dir = "tests/mapsrc"
    original_filename = os.path.join(map_dir, f"{filename}.vmf")
    saved_filename = os.path.join(map_dir, f"{filename}_resaved.vmf")
    vmf_tool.Vmf.from_file(original_filename).save_as(saved_filename)
    # recollect both .vmfs post-save
    # TODO: confirm original_vmf was not altered
    original_vmf = vmf_tool.Vmf.from_file(original_filename)
    saved_vmf = vmf_tool.Vmf.from_file(saved_filename)

    # assert len(saved_vmf.import_errors) == len(original_vmf.import_errors)
    assert len(saved_vmf.brushes) == len(original_vmf.brushes)
    for saved_brush, original_brush in zip(saved_vmf.brushes, original_vmf.brushes):
        for saved_face, original_face in zip(saved_brush, original_brush):
            # TODO: determine a margin of error for comparing brushes
            assert saved_face.plane == original_face.plane
    assert len(saved_vmf.entities) == len(original_vmf.entities)
    os.remove(saved_filename)  # delete saved file only if all tests succeed
    # NOTE: use `diff -u -w src.vmf dest.vmf` on linux to compare files
    saved_filename_vmx = saved_filename[:-1] + "x"
    if os.path.exists(saved_filename_vmx):
        os.remove(saved_filename_vmx)


def test_generate_blank():
    vmf_tool.Vmf("tests/mapsrc/untitled.vmf").save()
    if os.path.exists("tests/mapsrc/untitled.vmx"):
        os.remove("tests/mapsrc/untitled.vmx")


def test_connections():  # ISSUE #13  (Unwanted removal of duplicate keys...)
    test2_vmf = vmf_tool.Vmf.from_file("tests/mapsrc/test2.vmf")
    cp1 = [e for e in test2_vmf.entities.values() if dict(e.properties).get("targetname", None) == "cp1"][0]
    # ^ need a more convenient way of accessing entities by name
    cp1_connections = {n.name: n for n in cp1.nodes}["connections"].properties
    assert len([k for k, v in cp1_connections if k == "OnCapTeam1"]) == 2
    assert len([k for k, v in cp1_connections if k == "OnCapTeam2"]) == 2
