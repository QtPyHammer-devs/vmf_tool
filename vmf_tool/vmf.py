import os
import shutil
from typing import Dict, List, Set, Union

from .parser import Namespace, parse, text_from
from .brushes import Solid


class Vmf:
    def __init__(self, filename: str) -> Namespace:
        # how could a loading bar measure progress?
        self.filename: str = filename
        with open(self.filename, "r") as vmf_file:
            self.raw_namespace: Namespace = parse(vmf_file)
        # map raw.namespace with parser.scope
        # use Vmf @property to mutate the namespace directly
        # allowing for a remapped .vmf with edit history

        # Worldspawn:
        self.skybox: str = self.raw_namespace.world.skyname
        self.detail_material: str = self.raw_namespace.world.detailmaterial
        self.detail_vbsp: str = self.raw_namespace.world.detailvbsp

        self.raw_brushes: Dict[int, Namespace] = dict()
        # ^ {id: brush}
        if hasattr(self.raw_namespace.world, "solid"):
            self.raw_namespace.world.solids = [self.raw_namespace.world.solid]
        if hasattr(self.raw_namespace.world, "solids"):
            for brush in self.raw_namespace.world.solids:
                self.raw_brushes[int(brush.id)] = brush

        self.entities: Dict[int, Namespace] = dict()
        # ^ {id: entity}
        if hasattr(self.raw_namespace.world, "entity"):
            entity = self.raw_namespace.world.entity
            self.entities[int(entity.id)] = entity
        elif hasattr(self.raw_namespace.world, "entities"):
            for entity in self.raw_namespace.world.entities:
                self.entities[int(entity.id)] = entity

        self.brush_entities: Dict[int, Set[int]] = dict()
        # ^ {entity.id: {brush.id, brush.id, ...}}
        for entity_id, entity in self.entities.items():
            if hasattr(entity, "solid"):
                if not isinstance(entity, str):
                    entity.solids = [entity.solid]
            if hasattr(entity, "solids"):
                self.brush_entities[entity.id] = set()
                for brush in entity.solids:
                    if not isinstance(entity, str):
                        brush_id = int(entity.solid.id)
                        self.raw_brushes[brush_id] = entity.solid
                        self.brush_entities[entity_id].add(brush_id)

        self.import_errors: List[str] = list()
        self.brushes: Dict[int, Solid] = dict()
        # ^ {brush.id: brush}
        for i, brush_id in enumerate(self.raw_brushes):
            try:
                brush = Solid(self.raw_brushes[brush_id])
            except Exception as exc:
                self.import_errors.append("\n".join(
                    [f"Solid #{i} id: {brush_id} is invalid.",
                     f"{exc.__class__.__name__}: {exc}"]))
            else:
                self.brushes[brush_id] = brush

        # groups
        # user visgroups
        # worldspawn data

    def save_to_file(self, filename: Union[str, None] = None):
        # first, ensure all user edits will be represented in the saved file!
        if filename is None:
            filename = self.filename
        if os.path.exists(filename):
            base_filename, ext = os.path.splitext(filename)
            shutil.copy(filename, f"{base_filename}.vmx")
        with open(filename, "w") as file:
            file.write(text_from(self.raw_namespace))
