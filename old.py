#...

def rescale(a, b, x):
  sign=0
  if x>(a-1)/2: sign= 1
  if x<(a-1)/2: sign=-1
  return(2*b*x+b-a-b*sign)/(2*a)

#...

  def add(self, doors):
    self.doors = [mine or add for mine, add in zip(self.doors, doors.doors)]
#    self.doors[0] = self.doors[0] or doors.doors[0]
#    self.doors[1] = self.doors[1] or doors.doors[1]
#    self.doors[2] = self.doors[2] or doors.doors[2]
#    self.doors[3] = self.doors[3] or doors.doors[3]

#...

class Level:
  'Contains a 2-D list of rooms'
#  def __init__(self, width, length, minRoomWidth, maxRoomWidth, minRoomLength, maxRoomLength):
  def __init__(self, type, name, width, length, roomWidth, roomLength):
#  def __init__(self, arg0, arg1=0, arg2=0, arg3=0, arg4=0):
#    type = arg0
#    if type == DEFAULT_LEVEL: width, length, roomWidth, roomLength = arg1, arg2, arg3, arg4
#    if type == CUSTOM_LEVEL:
#      level = arg1
#      width = len(level[0])
#      length = len(level)
#      return
    log(7, '    ===== new Level '+str(width)+'x'+str(length)+' =====')
    log(7, '    type (unused)', type)
    log(7, '    name', name)
    self.name = name
    self.width = width
    self.length = length
    self.level = []
    for y in range(length): # make a 2-D list of rooms
      row = []
      for x in range(width):
#        roomWidth = random.randint(minRoomWidth, maxRoomWidth)
#        roomLength = random.randint(minRoomLength, maxRoomLength)
        room = Room(roomWidth, roomLength)
#        room = Room(roomWidth+random.randint(0,5), roomLength+random.randint(0,5))
        row.append(room)
      self.level.append(row)

#...

    dx = [-1, 0, 1, 1,  1,  0, -1, -1]
    dy = [ 1, 1, 1, 0, -1, -1, -1,  0]
    for i in range(8):
      if key == options[i][2]: return self.move(dx[i], dy[i], creatures)

#    if key == options[0][2]: return self.move(-1, 1, creatures)
#    if key == options[1][2]: return self.move( 0, 1, creatures)
#    if key == options[2][2]: return self.move( 1, 1, creatures)
#    if key == options[3][2]: return self.move( 1, 0, creatures)
#    if key == options[4][2]: return self.move( 1,-1, creatures)
#    if key == options[5][2]: return self.move( 0,-1, creatures)
#    if key == options[6][2]: return self.move(-1,-1, creatures)
#    if key == options[7][2]: return self.move(-1, 0, creatures)

#...

      miniWin.addch(2+y*3,5+x*5, char)

      #if doors.getTop() and y>0: miniWin.addch(roomDispY-1+y*3,3+x*5, '|')
      #if doors.getBottom() and y<levelLength-1: miniWin.addch(roomDispY+1+y*3,3+x*5, '|')
      #if doors.getLeft() and x>0: miniWin.addch(roomDispY+y*3,1+x*5, '-')
      #if doors.getRight() and x<levelWidth-1: miniWin.addch(roomDispY+y*3,5+x*5, '-')

#...

    upX = random.randrange(self.width)
    upY = random.randrange(self.length)
    downX = upX
    downY = upY
    while upX==downX and upY==downY:
      downX = random.randrange(self.width)
      downY = random.randrange(self.length)

#...

  def findStairs(self, up):
    char = DOWN_STAIRS_ID
    if up: char = UP_STAIRS_ID
    return self.findChar(char)

#...

  def findStairs(self, location, upStairs): #TODO remove this
    z = location.getZ()
    level = self.getLevel(z)
    levelX, levelY, roomX, roomY = level.findStairs(upStairs)
    location.setLevelXY(levelX, levelY)
    location.setRoomXY(roomX, roomY)
    return location
  def loadLevel(self, i, upStairs): #TODO remove this
    level = self.getLevel(i)
    levelWidth, levelLength = level.getWL()
    levelX, levelY, roomX, roomY = level.findStairs(upStairs)
    room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
    return level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY

#...

  def getLevelXY(self):        return self.levelX, self.levelY
  def setLevelXY(self, levelX, levelY):
    self.levelX = levelX
    self.levelY = levelY
  def getRoomXY(self): return self.roomX, self.roomY
  def setRoomXY(self, roomX, roomY):
    self.roomX = roomX
    self.roomY = roomY
  def getZ(self):      return self.z

#...

  def setZ(self, z):
    difference = z - self.z
    self.z = z
    if difference > 0: self.loadLevel(True)
    if difference < 0: self.loadLevel(False)
  def move(self, dx, dy, creatures):    
    if dx==0 and dy==0: return False
    level = self.getLevel()
    levelWidth, levelLength = level.getWL()
    room = self.getRoom()
    roomWidth, roomLength = room.getWL()
    x2=self.roomX+dx
    y2=self.roomY+dy
    if x2<-1 or x2>roomWidth or \
    y2<-1 or y2>roomLength:
      return False
    terrain = room.getTile(self.roomX, self.roomY).getTerrain()
    newTerrain = room.getTile(limit(x2, 0, roomWidth-1), limit(y2, 0, roomLength-1)).getTerrain()
    if newTerrain in solid:
#     if self.getName() != 'player': #uncomment to walk through walls
      return False
    #if moving diagonally and standing on a door or attempting to move on to one
    if dx != 0 and dy != 0 and DOOR_ID in [terrain, newTerrain]:
      return False
    enemy = creatures.findAt(self.z, self.levelX, self.levelY, x2, y2)
    if not enemy == None:
      #if self.attack(enemy): return True
      enemy.getStats().takeDamage(1) #TODO different amounts of damage, only attack enemies
      return True
    self.setRoomXY(x2, y2)
    if self.roomX<0 and self.levelX>0:
      self.levelX-=1
      oldRoomLength = roomLength
      room, roomWidth, roomLength = level.loadRoom(self.levelX, self.levelY)
      self.roomX=roomWidth-1
      if not roomLength == oldRoomLength: self.roomY = int(roomLength/2)
    elif self.roomX>roomWidth-1 and self.levelX<levelWidth-1:
      self.levelX+=1
      oldRoomLength = roomLength
      room, roomWidth, roomLength = level.loadRoom(self.levelX, self.levelY)
      self.roomX=0
      if not roomLength == oldRoomLength: self.roomY = int(roomLength/2)
    elif self.roomY<0 and self.levelY>0:
      self.levelY-=1
      oldRoomWidth = roomWidth
      room, roomWidth, roomLength = level.loadRoom(self.levelX, self.levelY)
      if not roomWidth == oldRoomWidth: self.roomX = int(roomWidth/2)
      self.roomY=roomLength-1
    elif self.roomY>roomLength-1 and self.levelY<levelLength-1:
      self.levelY+=1
      oldRoomWidth = roomWidth
      room, roomWidth, roomLength = level.loadRoom(self.levelX, self.levelY)
      if not roomWidth == oldRoomWidth: self.roomX = int(roomWidth/2)
      self.roomY=0
    self.roomX = limit(self.roomX, 0, roomWidth-1)
    self.roomY = limit(self.roomY, 0, roomLength-1)
    return True

#...

def doublerange(arg0, arg1=0):
  if arg1 == 0 and arg0.__class__ in [tuple, list]:
    xlen = arg0[0]
    ylen = arg0[1]
  else:
    xlen = arg0
    ylen = arg1
  return itertools.product(range(xlen), range(ylen))

#...

  def removeDead(self): # Bring out your dead!
#    i=0
#    while i < len(self.creatures)-1:
#      if not self.creatures[i].getStats().isAlive():
#        self.creatures.pop(i)
#      else:
#        i += 1

    #rebuild the list, excluding creatures that return false for isAlive()
    self.creatures = [creature for creature in self.creatures if creature.getStats().isAlive()]

#...

  def findAt(self, location):
    for creature in self.creatures:
      if location == creature.getLocation(): return creature
    return None

#...

    log(4, '    Level layout:')
    for y in range(self.length):
      line = ''
      for x in range(self.width):
        if (x==self.upX and y==self.upY) or (x==self.downX and y==self.downY):
          line += '2'
        else:
          line += str(minimap.getMiniroom(x,y).getMiddle())
      log(4,'    '+line+'    y:'+str(y))
    log(4, '')

#...

  def getStartingLocation(self):
    level = self.getLevel(0)
    levelX, levelY, roomX, roomY = level.findChar(UP_STA$
    location = Location(0, levelX, levelY, roomX, roomY)
    return location

#...

def randomLevel(name):
  levelWidth = random.randint(4,6)
  levelheight = random.randint(3,5)
  roomWidth = randSkip(7,17)
  roomLength = randSkip(7,15)
  level = Level(name, DEFAULT_LEVEL, levelWidth, levelhe$
  return level
class Location:
  'The location of a creature'
  def __init__(self, z, levelX, levelY, roomX, roomY):
    self.z = z
    self.setLevelXY(levelX, levelY)
    self.setRoomXY(roomX, roomY)
  def getZ(self):            return self.z
  def setZ(self, z):         self.z = z
  def changeZ(self, amount): self.z += amount

  def getLevelXY(self): return self.levelX, self.levelY
  def setLevelXY(self, levelX, levelY):
    self.levelX = levelX
    self.levelY = levelY
  def changeLevelX(self, amount): self.levelX += amount
  def changeLevelY(self, amount): self.levelY += amount

  def getRoomXY(self): return self.roomX, self.roomY
  def setRoomXY(self, roomX, roomY):
    self.roomX = roomX
    self.roomY = roomY
  def changeRoomX(self, amount): self.roomX += amount
  def changeRoomY(self, amount): self.roomY += amount

#...

#TODO change stats to a dictionary
class Stats: #TODO add a lot of stats including difficulty/experience levels
  'All the stats of a creature, including health and attributes but not location.'
  def __init__(self, health, maxHealth):
    self.health = health
    self.maxHealth = maxHealth
    self.healthTimer = 0
  def getHealth(self): return self.health
  def getMaxHealth(self): return self.maxHealth
  def changeMaxHealth(self, amount):
    self.maxHealth += amount
    if self.maxHealth < 0: self.maxHealth = 0
    self.health = limit(self.health, 0, self.maxHealth)
  def takeDamage(self, amount):
    #TODO apply armor
    self.changeHealth(-amount)
  def changeHealth(self, amount):
    self.health += amount
    self.health = limit(self.health, 0, self.maxHealth)
  def isAlive(self): return self.health > 0
  def display(self, screen, y, x):
    i = int(self.health * (len(healthColors)-1.0) / self.maxHealth)
    screen.addstr(y,x, 'HP:')
    screen.addstr(y,x+3, str(self.health)+'/'+str(self.maxHealth), curses.color_pair(healthColors[i]))
  def act(self):
    self.healthTimer -= 1
    if self.healthTimer < 1:
      self.healthTimer = 10
      self.changeHealth(1)

#...

class Doors:
  'Stores info about which of the 4 directions are active'
  def __init__(self, left, right, top, bottom):
    self.doors = [left, right, top, bottom]
  def getIndex(self, i):       return self.doors[i]
  def setIndex(self, i, value):        self.doors[i] = value
  def getLeft(self):           return self.doors[0]
  def getRight(self):          return self.doors[1]
  def getTop(self):            return self.doors[2]
  def getBottom(self):         return self.doors[3]
  def setLeft(self, left):     self.doors[0] = left
  def setRight(self, right):   self.doors[1] = right
  def setTop(self, top):       self.doors[2] = top
  def setBottom(self, bottom): self.doors[3] = bottom
  def getInverse(self): #swap left with right and top with bottom
    return Doors(self.doors[1], self.doors[0], self.doors[3], self.doors[2])
  def add(self, doors):
    self.doors = [mine or add for mine, add in zip(self.doors, doors.doors)]

#...

class Miniroom:
  def __init__(self, shown, middle, color, doors, visible):
    self.shown = shown
    self.middle = middle
    self.color = color
    self.doors = doors #openings in the wall
    self.visible = visible #visible walls
  def isShown(self):            return self.shown
  def getMiddle(self):          return self.middle
  def setMiddle(self, middle):  self.middle = middle
  def getColor(self):           return self.color
  def setColor(self, color):    self.color = color
  def getDoors(self):           return self.doors
  def getVisibleWalls(self):    return self.visible
                                    
#...

    template = ( #template defines the smallest room
    ( 8, 6, 9),
    ( 7, 1, 7),
    (10, 6,11))
    self.room = []
    for y in range(self.length): #construct the room row by row
      row = []
      for x in range(self.width):
        templateX = (x > 0) + (x == self.width - 1) #use template to find out which terrain to use
        templateY = (y > 0) + (y == self.length - 1)
        terrainID = template[templateY][templateX]
        row.append(Tile(terrainID, 0, [], True))
      self.room.append(row)
    self.fillCorners(corners, hallwayWidth)
  def fillCorners(self, corners, hW):

#...

def jsondefault(o):
  if isinstance(o, set):
    return list(o)
  return o.__dict__

def jsonLog(priority, obj):
  log(priority, repr(json.dumps(obj, indent=4, default=jsondefault)))

def jsonWrite(obj, filename):
#  jsonLog(1, obj)
#  return
  with open(filename, 'w') as f:
    f.write(json.dumps(obj, default=jsondefault))

def jsonRead(filename):
  with open(filename, 'r') as f:
                        
#...

   #TODO use *args for Level.__init__()
   #  def __init__(self, type, name, args*arg0=0, arg1=0, arg2=0, arg3=0): #TODO use *args for Level.__init__()
   #  def __init__(self, type, name, width, length, roomWidth, roomLength):
   #    log(7, '    == == = new Level  == == =')
   #    log(7, '    type', type)
   #...


#...

  z = plpos['z']
  levelX = plpos['levelX']
  levelY = plpos['levelY']
  roomX = plpos['roomX']
  roomY = plpos['roomY']

#...

    #Disabled since it does not work on weirdly-shaped rooms
    """for x in range(self.width): #top row
      topTile = self.room[0][x] #get the tile
      if not topTile.isShown(): shown.setTop(False) #if the tile is hidden, the wall is considered not visible
      elif topTile.getTerrain() == DOOR_ID: shown.setTop(True); break
      #otherwise if the wall has a door, the wall is visible and it overrides hidden tiles

    for x in range(self.width): # bottom row
      bottomTile = self.room[self.length-1][x]
      if not bottomTile.isShown(): shown.setBottom(False)
      elif bottomTile.getTerrain() == DOOR_ID: shown.setBottom(True); break

    for y in range(self.length): #left row
      leftTile = self.room[y][0]
      if not leftTile.isShown(): shown.setLeft(False)
      elif leftTile.getTerrain() == DOOR_ID: shown.setLeft(True); break

    for y in range(self.length): # right row
      rightTile = self.room[y][self.width-1]
      if not rightTile.isShown(): shown.setRight(False)
      elif rightTile.getTerrain() == DOOR_ID: shown.setRight(True); break
"""

#...

class Tile:
  'Contains the terrain and a list of items.'
  def __init__(self, terrainID, color, items, shown):
  #TODO make terrain an item
    self.terrainID = terrainID
    self.color = color
    self.items = items
    self.shown = shown
  #terrain is the material that is seen
  def getTopID(self):
    if len(self.items) == 0: return self.terrainID
    return self.items[-1].getID()
  def getTopColor(self):
    if len(self.items) == 0: return self.color
    return self.items[-1].getColor()
  def setTerrain(self, ID):     self.terrainID = ID
  def getTerrain(self):         return self.terrainID
  def setColor(self, color):    self.color = color
  def getColor(self):           return self.color
  def setItems(self, items):    self.items = items
  def getItems(self):           return self.items
  def addItem(self, item):      self.items.append(item)
  def popItem(self):            return self.items.pop()
  def show(self):               self.shown = True
  def hide(self):               self.shown = False
  def isShown(self):            return self.shown #TODO Tile.isShown() might need to be on each creature

#...

  def addDoors(self, doors):
    self.doors = addCards(self.doors, doors) #combine the current doors and the new doors info
    for x, y in doublerange(self.width, self.length): #add the doors to the actual room
      #TODO door creation is incorrect
      if doors[WEST] and abs(y - (self.length - 1) / 2.0) < 1 and x == 0 \
      or doors[EAST] and abs(y - (self.length - 1) / 2.0) < 1 and x == self.width - 1 \
      or doors[NORTH] and abs(x - (self.width - 1) / 2.0) < 1 and y == 0 \
      or doors[SOUTH] and abs(x - (self.width - 1) / 2.0) < 1 and y == self.length - 1: #TODO improve door creation $
        tile = self.getTile(x, y)
        tile.ID = DOOR_ID
        tile.color = DOOR_COLOR

#...

  z = pos['z']
  levelX = pos['levelX']
  levelY = pos['levelY']
  roomX = pos['roomX']
  roomY = pos['roomY']

#...

  def findAt(self, z, levelX, levelY, roomX, roomY): #TODO replace findAt() with findAtPos()
    for creature in self.creatures:
      pos = creature.getPos()
      if pos['z'] != z: continue
      if pos['levelX'] != levelX: continue
      if pos['levelY'] != levelY: continue
      if pos['roomX'] != roomX: continue
      if pos['roomY'] != roomY: continue
      return creature
    return None

#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...


#...
