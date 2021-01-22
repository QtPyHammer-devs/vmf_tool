import os

import vmf_tool


class TestVmfMethods:
    def test_load_from_file(self):
        test2 = vmf_tool.Vmf.from_file("tests/mapsrc/test2.vmf")
        assert len(test2.import_errors) == 0

    def test_save_to_file(self):
        original_filename = "tests/mapsrc/test2.vmf"
        folder = os.path.dirname(original_filename)
        filename = os.path.basename(original_filename)

        saved_filename = os.path.join(folder, f"test_save_{filename}")
        vmf_tool.Vmf.from_file(original_filename).save_as(saved_filename)

        # assert the saved file has the same objects with "close-enough" attributes
        # 1 to 1 text accuracy isn't nessecary

        # TODO: refactor
        original_vmf = vmf_tool.Vmf.from_file(original_filename)
        saved_vmf = vmf_tool.Vmf.from_file(saved_filename)
        os.remove(saved_filename)
        # TODO: delete saved_filename.vmx if it exists

        assert len(saved_vmf.import_errors) == len(original_vmf.import_errors)
        assert len(saved_vmf.brushes) == len(original_vmf.brushes)
        for saved_brush, original_brush in zip(saved_vmf.brushes, original_vmf.brushes):
            for saved_face, original_face in zip(saved_brush, original_brush):
                assert saved_face.plane == original_face.plane

    def test_connections(self):
        # Issue #13: Unwanted removal of duplicate keys on connections
        test2_vmf = vmf_tool.Vmf.from_file("tests/mapsrc/test2.vmf")
        cp1 = [e for e in test2_vmf.entities.values() if getattr(e, "targetname", None) == "cp1"][0]
        # ^ need a more convenient way of accessing entities by name
        assert len(cp1.connections.OnCapTeam1) == 2
        assert len(cp1.connections.OnCapTeam2) == 2
