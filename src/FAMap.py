import random

import FAModels
from sectors import MapSector, WallMapSector, DoorMapSector, DebugMapSector

def get_2d_random(
    xmax,
    ymax,
    xmin=0,
    ymin=0,
    near=None,
    min_distance=0,
    max_distance=0
):
    """Generate an (x, y) coordinate tuple somewhere in the specified
    rectangle."""
    given_xmax = xmax 
    given_ymax = ymax 

    if near is not None:
        xmin = near[0] + min_distance
        ymin = near[1] + min_distance
        xmax = near[0] + max_distance
        ymax = near[1] + max_distance
        if xmax > given_xmax:
            xmax = given_xmax
        if ymax > given_ymax:
            ymax = given_ymax
        if xmin > xmax:
            xmin = xmax
        if ymin > ymax:
            ymin = ymax

    x = random.randint(xmin, xmax)
    y = random.randint(ymin, ymax)

    return x, y

class Room:
    def __init__(self, x0, y0, xmax, ymax, min_room_size, max_room_size):
        # Upper left hand corner of the room
        self.x0 = x0
        self.y0 = y0
        # Map dimensions
        self.xmin = 0
        self.xmax = xmax
        self.ymin = 0
        self.ymax = ymax
        # Room dimensions
        self.min_room_size = min_room_size
        self.max_room_size = max_room_size
        self.max_doors = 2

        self.room = self.make_room()

    def get_corners(self, room=None):
        """Grab the absolute corner coordinates.
        
        :param room: if room is None, a new random corner is picked. if given
            room, return the absolute coords of the room's bottom right as
            corner2"""
        corner1 = (self.x0, self.y0)
        if room is None:
            corner2 = get_2d_random(
                self.xmax,
                self.ymax,
                near=corner1,
                min_distance=self.min_room_size,
                max_distance=self.max_room_size
            )
        else:
            corner2 = map(
                sum,
                zip(
                    corner1,
                    (len(room) - 1, len(room[0]) - 1)
                )
            )

        return corner1, corner2

    def make_room(self):
        """Randomly generate a room area. Draw the walls and doors for the
        room."""
        c1, c2 = self.get_corners()
        # c1 is guarenteed to be 'bigger' than c2
        x1, y1 = c1
        x2, y2 = c2
        # Make a zero-indexed room
        room = []
        for x in range(x2 - x1):
            room_column = []
            for y in range(y2 - y1):
                room_column.append(MapSector("msector-{0}-{1}".format(x, y)))
            room.append(room_column)

        walls = self.get_room_walls(room)
        for t in walls:
            x, y = t
            room[x][y] = WallMapSector("wallmsector-{0}-{1}".format(x, y))

        room = self.make_doors(room)

        return room

    def get_room_walls(self, room, no_corners=False):
        wall_sectors = []
        xmax = len(room) - 1
        ymax = len(room[0]) - 1
        for x in range(len(room)):
            for y in range(len(room[0])):
                if no_corners:
                    if (x in [0, xmax]) != (y in [0, ymax]):
                        wall_sectors.append((x, y))
                else:
                    if (x in [0, xmax]) or (y in [0, ymax]):
                        wall_sectors.append((x, y))
        return wall_sectors

    def make_doors(self, room):
        n = random.randint(1, self.max_doors)
        walls = self.get_room_walls(room, no_corners=True)
        for _ in range(n):
            x, y = random.choice(walls)
            room[x][y] = DoorMapSector("doormsector-{0}-{1}".format(x, y))
        return room

    def append_to_map_array(self, map_array):
        x1 = self.x0
        x2 = self.x0 + len(self.room)
        y1 = self.y0
        y2 = self.y0 + len(self.room[0])
        for x in range(x1, x2):
            for y in range(y1, y2):
                map_array[x][y] = self.room[x - x1][y - y1]

    def contains(self, px, py, overlap=0):
        """Determine whether the point (px, py) lies in the room+walls."""
        corner1, corner2 = self.get_corners(self.room)
        if (
            (corner1[0] <= px - overlap and corner2[0] >= px + overlap) and
            (corner1[1] <= py - overlap and corner2[1] >= py + overlap) 
        ):
            return True
        else:
            return False

    def contains_area(self, corner1, corner2, overlap=0):
        # Check if self contains at least one corner
        x1, y1 = corner1
        x2, y2 = corner2

        if (
            self.contains(x1, y1, overlap=overlap) or
            self.contains(x1, y2, overlap=overlap) or
            self.contains(x2, y1, overlap=overlap) or
            self.contains(x2, y2, overlap=overlap)
        ):
            return True
        else:
            return False
        

class MapCreator:
    def __init__(self):
        self.sizeX = 60
        self.sizeY = 25

    def make_impassable_areas(self, n_rooms=6):
        def is_acceptable_overlap(room, rooms, ok_overlap=1):
            if not rooms:
                return True
            for r in rooms:
                if (
                    r.contains_area(*room.get_corners()) or
                    room.contains_area(*r.get_corners())
                ):
                    return False
            return True

        min_room_size = 5
        max_room_size = 10
        xmax = self.sizeX
        ymax = self.sizeY
        rooms = []
        for _ in range(n_rooms):
            r = None
            while r is None or not is_acceptable_overlap(r, rooms):
                x, y = get_2d_random(
                    xmax - 1 - min_room_size,
                    ymax - 1 - min_room_size
                )
                r = Room(x, y, xmax, ymax, min_room_size, max_room_size)
            rooms.append(r)
        return rooms

    def createMap(self, _id):
        # Create the base tile
        mapArray = self.makeMapSectorArray( self.sizeX, self.sizeY )
        # randomly generate impassable areas
        rooms = self.make_impassable_areas()
        newMap = Map(_id, mapArray, rooms)

        return newMap

    def makeMapSectorArray(self, sizeX, sizeY):
        mapArray = []
        for x in range(sizeX):
            mapColumn = []
            for y in range(sizeY):
                mapColumn.append( MapSector("msector-" + str(x) + "-" + str(y)) )
            mapArray.append(mapColumn)

        return mapArray

class Map(FAModels.Model):
    def __init__(self, _id, mapSectorArray, rooms=None):
        self._id = _id
        self.mapSectorArray = mapSectorArray
        self.rooms = rooms
        if self.rooms is not None:
            for r in self.rooms:
                r.append_to_map_array(self.mapSectorArray)

    def get_random_player_start(self):
        while True:
            x, y = get_2d_random(
                len(self.mapSectorArray) - 1,
                len(self.mapSectorArray[0]) - 1
            )
            for r in self.rooms:
                if r.contains(x, y):
                    continue
            if not self.isPassable(x, y):
                continue
            return x, y

    def insertPlayer(self, player):
        x, y = self.get_random_player_start()
        map_sector = self.mapSectorArray[x][y]
        map_sector.addCharacter(player)
        player.setXY(x, y)
        player.setCurrentMap( self )

    def movePlayer(self, player, x, y):
        if not self.isPassable( x, y ):
            return player.getXY() 
        [plX, plY] = player.getXY() 
        self.mapSectorArray[plX][plY].removeCharacter( player )
        self.mapSectorArray[x][y].addCharacter( player )
        return [x, y]

    def isPassable(self, x, y):
        if not self.contains(x, y):
            return False
        return self.mapSectorArray[x][y].isPassable()

    def contains(self, x, y):
        if (x >= 0 and x < self.getWidth() and y >=0 and y < self.getHeight()):
            return True
        else:
            return False

    def getMapSectorArray(self):
        return self.mapSectorArray

    def getWidth(self):
        return len( self.mapSectorArray )

    def getHeight(self):
        return len( self.mapSectorArray[0] )
