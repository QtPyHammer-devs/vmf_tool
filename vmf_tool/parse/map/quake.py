# https://blenderartists.org/t/quake-map-exporter-for-blender3d/350073/8
# thanks to motorsep's comment in 2006 for providing links to .map specs

# http://www.gamers.org/dEngine/quake/QDP/qmapspec.html
# http://collective.valve-erc.com/index.php?go=map_format
# http://www.gamers.org/dEngine/quake/spec/quake-spec32.html

# http://www.garagegames.com/blogs/43612/11288
# ^ converter, QuArK & GTKRadiant compatible
import re

brushside = re.compile(r"\( (\d+ \d+ \d+) \) \( (\d+ \d+ \d+) \) \( (\d+ \d+ \d+) \) (\w+ \d+ \d+ \d+ \d+ \d+)")
# ^ A, B, C, texture = brushside.match(line).groups()
# A, B, C = [map(float, P.split()) for P in (A, B, C)]
# offset, scale = vector.Vec2(), vector.Vec2()
# offset.x, offset.y, rotation, scale.x, scale.y = texture.split()

# TODO: handle any and all floating points
