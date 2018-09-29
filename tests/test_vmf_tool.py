import unittest
import sys
sys.path.insert(0, '../')
import vmf_tool

fake_vmf = \
"""world
{
    solid
    {
    "id" "0"
    side
    {
        "material" "TOOLS/TOOLSNODRAW"
        "plane" "(64 0 0) (64 64 0) (0 64 0)"
    }
    side
    {
        "material" "TOOLS/TOOLSBLACK"
        "plane" "(64 0 64) (0 0 64) (0 64 64)"
    }
    editor
    {
        "colour" "255 0 255"
    {
    }
}"""


class TestPluralise(unittest.TestCase):
    
    def test_f(self):
        self.assertEqual(vmf_tool.pluralise('hoof'), 'hooves')

    def test_y(self):
        self.assetEqual(vmf_tool.pluralise('body'), 'bodies')

    def test_ex(self):
        self.assertEqual(vmf_tool.pluralise('vertex'), 'vertices')

    def test_other(self):
        self.assertEqual(vmf_tool.pluralise('horse'), 'horses')


class TestSingularise(unittest.TestCase):

    def test_ves(self):
        self.assertEqual(vmf_tool.singularise('hooves'), 'hoof')

    def test_ies(self):
        self.assertEqual(vmf_tool.singularise('bodies'), 'body')

    def test_ices(self):
        self.assertEqual(vmf_tool.singularise('vertices'), 'vertex')

    def test_other(self):
        self.assertEqual(vmf_tool.singularise('horses'), 'horse')


class TestScope(unittest.TestCase):
    complex_scope = vmf_tool.scope(['top', 1, 'inner'])
    
    def test_init(self):
        self.assertEqual(vmf_tool.scope().strings, [])
        self.assertEqual(complex_scope.strings(), ['top', 1, 'inner'])

    def test_len(self):
        self.assertEqual(len(complex_scope), 3)

    def test_repr(self):
        self.assertEqual(repr(complex_scope), "['top'][1]['inner']")

    def test_add(self):
        scope = vmf_tool.scope()
        scope.add('test')
        self.assertEqual(scope.strings, ['test'])
        scope.add('test2')
        self.assertEqual(scope.strings, ['test', 'test2'])

    def test_reduce(self):
        scope = vmf_tool.scope(['top', 0, 'sub', 'subsub', 1, 'item'])
        scope.remove(1)
        self.assertEqual(scope.strings(), ['top', 0, 'sub', 'subsub', 1])
        scope.remove(2)
        self.assertEqual(scope.strings(), ['top', 0])


class TestNamespaceFromFile(unittest.TestCase):
    global fake_vmf
    fake_vmf_ns = vmf_tool.namespace_from(fake_vmf)

    def test_fake_vmf(self):
        keylist = lambda x: list(x.__dict__.keys())
        self.assertEqual(keylist(fake_vmf_ns), ['world'])
        self.assertEqual(keylist(fake_vmf_ns.world), ['solid'])
        solid = fake_vmf_ns.world.solid
        self.assertEqual(keylist(solid), ['id', 'sides', 'editor'])
        self.assertEqual(solid.id, '0')
        self.assertEqual(len(solid.sides), 2)
        fake_side = {'material': 'None'}
        solid.sides.append(fake_side)
        self.assertEqual(solid.sides[-1], fake_side)


class TestNamespace(unittest.TestCase):

    def test_init(self):
        ...

    def test_setitem(self):
        ...

    def test_getitem(self):
        ...

    def test_iter(self):
        ...

    def test_len(self):
        ...

    def test_repr(self):
        ...


class TestDictFromNamespace(unittest.TestCase):

    def test_nested_dict(self):
        ...
    
class TestExport(unittest.TestCase):
    
    def test_export(self):
        # load vmf
        # convert to namespace
        # export to file
        # read files
        ...

        
if __name__ == "__main__":
    unittest.main()
