from __future__ import annotations

import os
import shutil
import traceback
from typing import Any, Dict, List, Set

from . import solid
from .parse import common
from .parse import vmf as parse_vmf


class Vmf:
    _vmf: common.Namespace
    brush_entities: Dict[int, List[int]]
    brushes: Dict[int, solid.Brush]
    detail_material: str = "detail/detailsprites"
    detail_vbsp: str = "detail.vbsp"
    entities: Dict[int, common.Namespace]
    filename: str
    hidden: Dict[str, Set[int]]
    import_errors: Dict[str, str]
    raw_brushes: Dict[int, common.Namespace]
    skybox: str = "sky_tf2_04"
    # TODO: setters to update self._vmf properties
    # TODO: convenience method / property for modifying entities by name

    def __init__(self, filename: str):
        self.filename = filename
        # create base .vmf
        worldspawn = common.Namespace(id="1", mapversion="0", classname="worldspawn", solid=[],
                                      detailmaterial=self.detail_material, detailvbsp=self.detail_vbsp,
                                      maxpropscreenwidth="-1", skyname=self.skybox)
        self._vmf = common.Namespace(world=worldspawn, entity=[])
        # clear all dicts
        self.brush_entities = dict()
        self.brushes = dict()
        self.entities = dict()
        self.hidden = {"brushes": set(), "entities": set()}
        # ^ {"brushes": [brush.id], "entities": [entity.id]}
        self.import_errors = dict()
        self.raw_brushes = dict()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.filename}>"

    @staticmethod
    def from_file(filename) -> Vmf:
        out = Vmf(filename)
        # TODO: yield progress for a loading bar
        with open(filename, "r") as vmf_file:
            out._vmf = parse_vmf.as_namespace(vmf_file.read())

        out.cleanup_namespace()
        out.load_world_brushes()
        out.load_entities()  # & brushes tied to entities
        out.convert_solids()  # out.raw_brushes: common.Namespace -> out.brushes: brushes.Brush

        # groups
        # user visgroups

        out.skybox = out._vmf.world.skyname
        out.detail_material = out._vmf.world.detailmaterial
        out.detail_vbsp = out._vmf.world.detailvbsp
        return out

    def cleanup_namespace(self):
        def list_if_not(unknown) -> List[Any]:
            if not isinstance(unknown, list):
                unknown = [unknown]
            return unknown

        # world brushes
        self._vmf.world.solid = list_if_not(getattr(self._vmf.world, "solid", []))
        # TODO: groups (self._vmf.world.group)
        # hidden world brushes
        self._vmf.world.hidden = list_if_not(getattr(self._vmf.world, "hidden", []))
        # entities
        self._vmf.entity = list_if_not(getattr(self._vmf, "entity", []))
        # brush entities' brushes
        for i, entity in enumerate(self._vmf.entity):
            self._vmf.entity[i].solid = list_if_not(getattr(entity, "solid", []))
            self._vmf.entity[i].hidden = list_if_not(getattr(entity, "hidden", []))
        # hidden entities
        self._vmf.hidden = list_if_not(getattr(self._vmf, "hidden", []))
        # hidden brush entities' brushes
        for i, namespace in enumerate(self._vmf.hidden):
            self._vmf.hidden[i].entity.solid = list_if_not(getattr(namespace.entity, "solid", []))
            self._vmf.hidden[i].entity.hidden = list_if_not(getattr(namespace.entity, "hidden", []))

    def load_world_brushes(self):
        """move world solids from namespace to self"""
        self.raw_brushes = {int(b.id): b for b in getattr(self._vmf.world, "solid", list())}
        hidden = getattr(self._vmf.world, "hidden", list())
        for namespace in hidden:
            self.raw_brushes[int(namespace.solid.id)] = namespace.solid
            self.hidden["brushes"].add(int(namespace.solid.id))

    def load_entities(self):
        """move entities to self & collect solids from brush based entities"""
        self.entities = {int(e.id): e for e in getattr(self._vmf, "entity", list())}
        # ^ {entity.id: entity}
        hidden = getattr(self._vmf, "hidden", list())
        for namespace in hidden:
            self.hidden["entities"].add(int(namespace.entity.id))
            self.entities[int(namespace.entity.id)] = namespace.entity
        self.brush_entities = dict()
        # ^ {entity.id: [brush.id, brush.id, ...]}
        for entity_id, entity in self.entities.items():
            hidden = getattr(entity, "hidden", list())
            for namespace in hidden:
                self.hidden["brushes"].add(int(namespace.solid.id))
                entity.add_attr("solid", namespace.solid)
            if hasattr(entity, "solid"):
                if any([isinstance(b, common.Namespace) for b in entity.solid]):
                    entity_brushes = {b.id: b for b in entity.solid if isinstance(b, common.Namespace)}
                    self.raw_brushes.update(entity_brushes)
                    self.brush_entities[entity_id] = list(entity_brushes.keys())

    def convert_solids(self):
        """self.raw_brushes: common.Namespace -> self.brushes: brushes.Brush"""
        self.import_errors = dict()
        # ^ {"Error text": traceback}
        self.brushes = dict()
        # ^ {brush.id: brush}
        for i, brush_id in enumerate(self.raw_brushes):
            try:
                brush = solid.Brush.from_namespace(self.raw_brushes[brush_id])
            except Exception as exc:
                error_text = f"Solid #{i} id: {brush_id} is invalid.\n{exc.__class__.__name__}: {exc}"
                self.import_errors[error_text] = traceback.format_exc()
            else:
                self.brushes[brush_id] = brush

    def save_as(self, filename: str = ""):
        """saves to self.filename if no filename is given"""
        # TODO: store hidden state of solids & entities
        # TODO: increment mapversion

        def is_world_brush(brush):
            return not any([brush.id in b_ids for b_ids in self.brush_entities.values()])

        self._vmf.world.solid = []
        self._vmf.world.hidden = []
        for brush in filter(is_world_brush, self.brushes.values()):
            if brush.id in self.hidden["brushes"]:
                self._vmf.world.hidden.append(brush.as_namespace)
            else:
                self._vmf.world.solid.append(brush.as_namespace())

        # self._vmf.world.hidden = []
        # for entity in self.entities.values():
        #    if entity.id in self.brush_entities:
        #        entity.brushes = [self.brushes[b.id] for b in self.brush_entities[entity.id]]
        #        # TODO: hide brushes within entity
        #        # UNTESTED: what do partially hidden brush_entities look like?
        #    # TODO: wrap entity in a "hidden" Namespace if needed
        #    self._vmf.entity.append(entity.as_namespace())

        # TODO: set self._vmf.world.quickhide.count

        if filename == "":  # default
            filename = self.filename
        if os.path.exists(filename):
            old_filename, ext = os.path.splitext(filename)
            shutil.copy(filename, f"{old_filename}.vmx")
        with open(filename, "w") as file:
            file.write(parse_vmf.as_vmf(self._vmf))
