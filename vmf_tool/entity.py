from __future__ import annotations

# TODO: use valvefgd for generating entities & generating help text
import valvevmf

# from . import vector


class BaseEntity:
    _source: valvevmf.VmfNode
    # TODO: inputs, outputs, addoutputs, flags, properties

    def __init__(self):
        self._source = valvevmf.VmfNode()
        raise NotImplementedError()

    @classmethod
    def from_node(cls: Entity, node: valvevmf.VmfNode) -> Entity:
        out = cls()
        out._source = node
        raise NotImplementedError()
        return out


# TODO: entity helper classes
# -- decal -> renderable geo (projected quad(s))
# -- overlay -> renderable geo (like decal, but with more controls)
# -- 3D coords -> vector.vec3

# TODO: generate a dict of entities from a .fgd
# -- {"classname": EntityClass}
# TODO: generate second dict of entity "editorclass" (for titanfall .fgds, once generated)
# -- {"classname: {"editorclass": EntityClass_editorclass}}
