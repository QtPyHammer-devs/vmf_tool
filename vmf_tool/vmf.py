from __future__ import annotations
import itertools
import os
import shutil
from typing import Dict, List, Set

import valvevmf

# TODO: from . import entity
from . import solid


# TODO: get defaults from external config dict
default = {
    "skybox": "sky_tf2_04",  # Team Fortress 2 default sky
    "detail_vbsp": "detail.vbsp",
    "detail_material": "detail/detailsprites"}
# TODO: default viewsettings

Entity = valvevmf.VmfNode


class Vmf:
    _source: valvevmf.Vmf
    entity_brushes: Dict[int, List[int]]
    # ^ {Entity.id, [Brush.id]}
    brushes: Dict[int, solid.Brush]
    # ^ {id: Brush}
    detail_material: str = default["detail_material"]
    detail_vbsp: str = default["detail_vbsp"]
    entities: Dict[int, Entity]
    # ^ {id: Entity}
    filename: str
    hidden: Dict[str, Set[int]]
    # ^ {"collection": {object.id}}
    skybox: str = default["skybox"]

    # TODO: entity targetname lookups
    # TODO: brush texture grouping
    # TODO: auto visgroups
    # TODO: dynamic grouping
    # TODO: hidden/unhidden state
    # TODO: confirm all ids are unique

    def __init__(self, filename: str):
        """creates a new .vmf; does not open an exising file"""
        self.filename = filename
        # create base .vmf
        self._source = valvevmf.Vmf()
        # copy of tests/mapsrc/blank.vmf
        nodes = [
            valvevmf.VmfNode(
                "versioninfo",
                properties=[
                    ("editorversion", 400),
                    ("editorbuild", 7803),
                    ("mapversion", 0),
                    ("formatversion", 100),
                    ("prefab", False)]),
            # TODO: viewsettings defaults from config
            valvevmf.VmfNode(
                "viewsettings",
                properties=[
                    ("bSnapToGrid", True),
                    ("bShowGrid", True),
                    ("bShowLogicalGrid", False),
                    ("nGridSpacing", 64),
                    ("bShow3DGrid", False)]),
            valvevmf.VmfNode(
                "world",
                properties=[
                    ("id", 1),
                    ("mapversion", 0),  # save revision?
                    ("classname", "worldspawn"),
                    ("detailmaterial", self.detail_material),
                    ("detailvbsp", self.detail_vbsp),
                    ("maxpropscreenwidth", -1),
                    ("skyname", self.skybox)]),
            valvevmf.VmfNode(
                "cameras",
                properties=[
                    ("activecamera", -1)]),
            valvevmf.VmfNode(
                "cordon",
                properties=[
                    ("mins", (-1024, -1024, -1024)),
                    ("maxs", (1024, 1024, 1024)),
                    ("active", 0)])]
        self._source.nodes = nodes
        # fresh dicts
        self.entity_brushes = dict()
        self.brushes = dict()
        self.entities = dict()
        self.hidden = {"brushes": set(), "entities": set()}
        # ^ {"brushes": [brush.id], "entities": [entity.id]}

    def __repr__(self):
        quick_stats = f"{len(self.brushes)} brushes & {len(self.entities)} entities"
        return f"<{self.__class__.__name__} {self.filename} ({quick_stats})>"

    @classmethod
    def from_file(cls: Vmf, filename: str) -> Vmf:
        out = cls(filename)
        # TODO: loading progress
        out._source = valvevmf.Vmf(filename)
        out.reload_world_brushes()
        out.reload_entities()  # extends self.brushes
        # TODO: index groups
        # TODO: index visgroups (user & auto)
        world_node = {n.name: n for n in out._source.nodes}["world"]
        world_properties = dict(world_node.properties)
        out.skybox = world_properties["skyname"]
        out.detail_material = world_properties["detailmaterial"]
        out.detail_vbsp = world_properties["detailvbsp"]
        # TODO: warn of any invalid solids & other errors (displacement in brush entity, overlapping ids etc.)
        return out

    def reload_world_brushes(self):
        """regenerate self.brushes from self._source"""
        self.hidden["brushes"] = set()
        self.brushes = dict()

        world_nodes = self._source.children("world")
        assert len(world_nodes) == 1
        worldspawn = world_nodes[0]

        for node in worldspawn.nodes:
            is_hidden = False
            if node.name == "hidden":
                is_hidden = True
                assert len(node.properties) == 0
                assert len(node.nodes) == 1
                node = node.nodes[0]
            if node.name == "solid":
                brush_id = dict(node.properties)["id"]
                if is_hidden:
                    self.hidden["brushes"].add(brush_id)
                assert brush_id not in self.brushes
                self.brushes[brush_id] = solid.Brush.from_node(node)

    def reload_entities(self):
        """regenerate self.entities & self.entity_brushes from self._source; also extends self.brushes"""
        self.hidden["entities"] = set()
        for brush_id in itertools.chain(*self.entity_brushes.keys()):
            self.hidden["brushes"].remove(brush_id)
        self.entity_brushes = dict()
        # ^ {Entity.id: {Brush.id}}
        self.entities = dict()
        # ^ {Entity.id: Entity}
        for node in self._source.nodes:
            is_hidden = False
            if node.name == "hidden":  # TODO: func
                is_hidden = True
                assert len(node.properties) == 0
                assert len(node.nodes) == 1
                node = node.nodes[0]
            if node.name == "entity":
                entity_id = dict(node.properties)["id"]
                if is_hidden:
                    self.hidden["entities"].add(entity_id)
                # assert entity_id not in self.entities
                if entity_id in self.entities:
                    raise RuntimeError("memory leak!")
                self.entities[entity_id] = node
                self.entity_brushes[entity_id] = set()
                for child_node in node.nodes:  # grab solid
                    child_is_hidden = False
                    if child_node.name == "hidden":  # TODO: func
                        child_is_hidden = True
                        assert len(child_node.properties) == 0
                        assert len(child_node.nodes) == 1
                        child_node = child_node.nodes[0]
                    if child_node.name == "solid":
                        brush_id = dict(child_node.properties)["id"]
                        self.entity_brushes[entity_id].add(brush_id)
                        brush = solid.Brush.from_node(child_node)
                        self.brushes[brush_id] = brush
                        if is_hidden or child_is_hidden:
                            self.hidden["brushes"].add(brush_id)

    def entity_id_of_brush(self, brush_id: int) -> int | None:
        """None if world brush"""
        brush_entity = {
            brush_id: entity_id
            for entity_id, brush_ids in self.brush_entitites.items()
            for brush_id in brush_ids}
        # ^ {Brush.id: Entity.id}
        return brush_entity.get(brush_id, None)

    def save(self):
        return self.save_as(self.filename)

    def save_as(self, filename: str):
        """saves to self.filename if no filename is given"""
        # update self._source
        _source_nodes = {n.name: n for n in self._source.nodes}
        # entities first
        entity_nodes = dict()
        # ^ {Entity.id: Entity.as_node()}
        for entity_id, entity in self.entities.items():
            entity_node = entity
            if entity_id in self.hidden:
                entity_node = valvevmf.VmfNode("hidden", nodes=[entity_node])
            entity_nodes[entity_id] = entity_node
        # brushes second
        ignored_world_nodes = [
            node
            for node in _source_nodes["world"].nodes
            if node.name not in ("solid", "hidden")]
        _source_nodes["world"].nodes = list()
        # collect brushes
        brush_entity = {
            brush_id: entity_id
            for entity_id, brush_ids in self.entity_brushes.items()
            for brush_id in brush_ids}
        # ^ {Brush.id: Entity.id}
        for brush in self.brushes.values():
            solid_node = brush.as_node()
            if brush.id in self.hidden["brushes"]:
                solid_node = valvevmf.VmfNode("hidden", nodes=[solid_node])
            if brush.id in brush_entity:  # attach to entity
                # NOTE: hidden brushes which are part of a hidden entity may not be counted
                entity_nodes[brush_entity[brush.id]].nodes.append(solid_node)
            else:  # world brush
                _source_nodes["world"].nodes.append(solid_node)
        _source_nodes["world"].nodes.extend(ignored_world_nodes)
        self._source = valvevmf.Vmf()
        # TODO: check with Hammer to see if scrambling the order of nodes affects anything
        if sum(map(len, self.hidden.values())) > 0:
            # NOTE: if all brushes of an entity are hidden the ent is wrapped in a `hidden` node
            # -- however, the individual brushes within that entity are not
            # TODO: confirm all variations on this and if we can get lazy with it
            quickhide_count = len(self.hidden["brushes"]) + len(self.hidden["entities"])
            _source_nodes["quickhide"] = valvevmf.VmfNode("quickhide", properties=[("count", quickhide_count)])
        elif "quickhide" in _source_nodes:
            _source_nodes.pop("quickhide")
        self._source.nodes = list(_source_nodes.values())
        self._source.nodes.extend(entity_nodes.values())
        # TODO: set self._vmf.world.quickhide.count
        # TODO: save changes to visgroup state (no clue how that works)
        # do the save
        # TODO: increment mapversion
        if os.path.exists(filename):
            old_filename, ext = os.path.splitext(filename)
            shutil.copy(filename, f"{old_filename}.vmx")
        with open(filename, "w") as file:
            file.write(self._source.vmf_str())
