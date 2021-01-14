import os

import vmf_tool


class TestVmfMethods:
    def test_save_to_file(self):
        first_filename = "tests/mapsrc/test2.vmf"
        folder = os.path.dirname(first_filename)
        filename = os.path.basename(first_filename)

        new_filename = os.path.join(folder, f"test_save_{filename}")
        vmf_tool.Vmf(first_filename).save_to_file(new_filename)

        with open(first_filename, "r") as first:
            first_vmf_text = first.read()

        with open(new_filename, "r") as saved:
            saved_vmf_text = saved.read()
        os.remove(new_filename)

        assert first_vmf_text == saved_vmf_text

    def test_connections(self):
        # Issue #13: Unwanted removal of duplicate keys on connections
        test2_vmf = vmf_tool.Vmf("tests/mapsrc/test2.vmf")
        cp1 = [e for e in test2_vmf.entities.values() if getattr(e, "targetname", None) == "cp1"][0]
        # ^ need a more convenient way of accessing entities by name
        assert len(cp1.connections.OnCapTeam1) == 2
        assert len(cp1.connections.OnCapTeam2) == 2
