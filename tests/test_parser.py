from vmf_tool import parser


class TestSkeletonKeyDict:
    def test_singulars(self):
        skd = parser.SkeletonKeyDict(id=4)
        assert skd["id"] == 4

    def test_plurals(self):
        skd = parser.SkeletonKeyDict(sides=[{"id": 5}, {"id": 6}, {"id": 7}])
        for side, correct_id in zip(skd.sides, (5, 6, 7)):
            assert side.id == correct_id
