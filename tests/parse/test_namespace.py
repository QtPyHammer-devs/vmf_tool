from vmf_tool.parse.common import Namespace


def test_init():
    # basic singulars
    assert Namespace([("key", "value")]).__dict__ == {"key": "value"}, "*args"
    assert Namespace([("key", "value"), ("key2", "value2")]).__dict__ == {"key": "value", "key2": "value2"}, "args"
    assert Namespace([("key", "value")], [("key2", "value2")]).__dict__ == {"key": "value", "key2": "value2"}, "args"
    assert Namespace(key="value").__dict__ == {"key": "value"}, "kwargs"
    assert Namespace(key="value", key2="value2").__dict__ == {"key": "value", "key2": "value2"}, "kwargs"
    assert Namespace([("key", "value")], key2="value2").__dict__ == {"key": "value", "key2": "value2"}, "args + kwargs"
    # basic plurals
    assert Namespace([("key", "value"), ("key", "value2")]).__dict__ == {"key": ["value", "value2"]}
