import os
import shutil
from typing import Dict, List, Set

from . import brushes
from . import parser


class Vmf:
    _vmf: parser.Namespace
    brush_entities: Dict[int, Set[int]]
    brushes: Dict[int, brushes.Solid]
    detail_material: str
    detail_vbsp: str
    entitites: Dict[int, parser.Namespace]
    filename: str
    import_errors: List[str]
    raw_brushes: Dict[int, parser.Namespace]
    skybox: str

    def __init__(self, filename: str):
        self.filename = filename
        if os.path.exists(self.filename):
            self.load()
        else:
            ...  # generate basic .vmf namespace
            # a real new file, not loading a template

    def load(self):
        # how could a loading bar measure progress?
        with open(self.filename, "r") as vmf_file:
            self._vmf = parser.parse(vmf_file)
        # map the raw Namespace with parser.scope
        # use Vmf @property to mutate the namespace directly
        # allowing for a remapped .vmf with edit history (CRDT support)

        self.load_world_brushes()
        self.load_entities()
        self.convert_solids()

        # groups
        # user visgroups
        # worldspawn data

        # Worldspawn:
        self.skybox = self._vmf.world.skyname
        self.detail_material = self._vmf.world.detailmaterial
        self.detail_vbsp = self._vmf.world.detailvbsp

    def load_world_brushes(self):
        """move world solids from namespace to self"""
        if hasattr(self._vmf.world, "solid"):
            self._vmf.world.solids = [self._vmf.world.solid]
            del self._vmf.world.solid
        self.raw_brushes = {int(b.id): b for b in getattr(self._vmf.world, "solids", list())}
        # ^ {id: brush}

    def load_entities(self):
        """move entities to self & collect solids from brush based entities"""
        if hasattr(self._vmf, "entity"):
            self._vmf.entities = [self._vmf.entity]
            del self._vmf.entity
        self.entities = {int(e.id): e for e in getattr(self._vmf, "entities", list())}
        # ^ {entity.id: entity}
        self.entities.update({e.targetname: e for e in self.entities.values() if hasattr(e, "targetname")})
        # ^ {entity.targetname: entity}
        # NOTE: entities can share targetnames, only the last entity with this name will return this way

        self.brush_entities = dict()
        # ^ {entity.id: {brush.id, brush.id, ...}}
        for entity_id, entity in self.entities.items():
            if isinstance(getattr(entity, "solid", None), parser.Namespace):
                entity.solids = [entity.solid]
                del entity.solid
            if hasattr(entity, "solids"):  # assuming at least one is a brush, & not a flag
                entity_brushes = {b.id: b for b in entity.solids if isinstance(b, parser.Namespace)}
                self.raw_brushes.update(entity_brushes)
                self.brush_entities[entity_id] = set(entity_brushes.keys())

    def convert_solids(self):
        """self.raw_brushes: parser.Namespace -> self.brushes: brushes.Solid"""
        self.import_errors = list()
        self.brushes = dict()
        # ^ {brush.id: brush}
        for i, brush_id in enumerate(self.raw_brushes):
            try:
                brush = brushes.Solid(self.raw_brushes[brush_id])
            except Exception as exc:
                self.import_errors.append("\n".join(
                    [f"Solid #{i} id: {brush_id} is invalid.",
                     f"{exc.__class__.__name__}: {exc}"]))
            else:
                self.brushes[brush_id] = brush

    def save_to_file(self, filename: str = ""):
        # first, ensure all user edits will be represented in the saved file!
        # -- copying changes made to self.brushes to self._vmf etc.
        # TODO: update self._vmf with changes
        if filename == "":
            filename = self.filename
        if os.path.exists(filename):
            old_filename, ext = os.path.splitext(filename)
            shutil.copy(filename, f"{old_filename}.vmx")
        with open(filename, "w") as file:
            file.write(parser.text_from(self._vmf))
