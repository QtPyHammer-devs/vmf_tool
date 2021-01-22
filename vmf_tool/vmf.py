from __future__ import annotations

import os
import shutil
import traceback
from typing import Dict, List

from . import brushes
from . import parser


class Vmf:
    _vmf: parser.Namespace
    brush_entities: Dict[int, List[int]]
    brushes: Dict[int, brushes.Brush]
    detail_material: str = "detail/detailsprites"
    detail_vbsp: str = "detail.vbsp"
    entities: Dict[int, parser.Namespace]
    filename: str
    hidden: Dict[str, List[int]]
    import_errors: Dict[str, str]
    raw_brushes: Dict[int, parser.Namespace]
    skybox: str = "sky_tf2_04"
    # TODO: setters to update self._vmf properties

    def __init__(self, filename: str):
        self.filename = filename
        # create base .vmf
        worldspawn = parser.Namespace(id="1", mapversion="0", classname="worldspawn", solid=[],
                                      detailmaterial=self.detail_material, detailvbsp=self.detail_vbsp,
                                      maxpropscreenwidth="-1", skyname=self.skybox)
        self._vmf = parser.Namespace(world=worldspawn, entity=[])
        # clear all dicts
        self.brush_entities = dict()
        self.brushes = dict()
        self.entities = dict()
        self.hidden = {"brushes": [], "entities": []}
        self.import_errors = dict()
        self.raw_brushes = dict()

    @staticmethod
    def from_file(filename) -> Vmf:
        out = Vmf(filename)
        # TODO: yield progress for a loading bar
        with open(filename, "r") as vmf_file:
            out._vmf = parser.parse(vmf_file)

        out.load_world_brushes()
        out.load_entities()  # & brushes tied to entities
        out.convert_solids()  # out.raw_brushes: parser.Namespace -> out.brushes: brushes.Brush

        # groups
        # user visgroups

        out.skybox = out._vmf.world.skyname
        out.detail_material = out._vmf.world.detailmaterial
        out.detail_vbsp = out._vmf.world.detailvbsp
        return out

    def load_world_brushes(self):
        """move world solids from namespace to self"""
        self.raw_brushes = {int(b.id): b for b in getattr(self._vmf.world, "solid", list())}
        # ^ {id: brush}
        # TODO: add hidden brush.ids to self.hidden["brushes"]

    def load_entities(self):
        """move entities to self & collect solids from brush based entities"""
        self.entities = {int(e.id): e for e in getattr(self._vmf, "entity", list())}
        # ^ {entity.id: entity}
        # TODO: convenience method / property for modifying entities by name
        self.brush_entities = dict()
        # ^ {entity.id: [brush.id, brush.id, ...]}
        for entity_id, entity in self.entities.items():
            if hasattr(entity, "solid"):
                if any([isinstance(b, parser.Namespace) for b in entity.solid]):
                    entity_brushes = {b.id: b for b in entity.solid if isinstance(b, parser.Namespace)}
                    self.raw_brushes.update(entity_brushes)
                    self.brush_entities[entity_id] = list(entity_brushes.keys())
        # TODO: add hidden entity & brush ids to self.hidden

    def convert_solids(self):
        """self.raw_brushes: parser.Namespace -> self.brushes: brushes.Brush"""
        self.import_errors = dict()
        # ^ {"Error text": traceback}
        self.brushes = dict()
        # ^ {brush.id: brush}
        for i, brush_id in enumerate(self.raw_brushes):
            try:
                brush = brushes.Brush.from_namespace(self.raw_brushes[brush_id])
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

        self._vmf.world.brush = []
        for brush in self.brushes.values():
            if is_world_brush(brush):
                self._vmf.world.brush.append(brush.as_namespace())

        # for entity in self.entities.values():
        #    if entity.id in self.brush_entities:
        #        entity.brushes = [self.brushes[b.id] for b in self.brush_entities[entity.id]]
        #    self._vmf.entity.append(entity.as_namespace())

        if filename == "":  # default
            filename = self.filename
        if os.path.exists(filename):
            old_filename, ext = os.path.splitext(filename)
            shutil.copy(filename, f"{old_filename}.vmx")
        with open(filename, "w") as file:
            file.write(self._vmf.as_string())
