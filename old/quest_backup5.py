#!/usr/bin/python
import os, random, math, time, curses, sys, itertools, pickle

startTime = time.time()
#chars = '.#^v!Os-*:++;[???---////TT(r)?[[[]]]]?ooooo???????'

#these are the ID numbers for different items and terrain
UP_STAIRS_ID = 3
DOWN_STAIRS_ID = 4
DOOR_ID = 12
MONSTER_ID = 13
BLOCK_ID = 5

DOOR_COLOR = 1

DEFAULT_LEVEL = 0 #TODO use level types
CUSTOM_LEVEL = 1
LEVEL_FROM_FILE = 2 #TODO town level at the top
#TODO add more constants


chars = [] #run initializeChars() to initialize these
#colors = []
def initializeChars():
  global chars, colors
  #these are the types of terrain and items

  chars = [	   ' ',	#  0
		   '.',	#  1
		   '@',	#  2
		   '<',	#  3
		   '>',	#  4
  curses.ACS_BLOCK,	#  5
  curses.ACS_HLINE,	#  6
  curses.ACS_VLINE,	#  7
  curses.ACS_ULCORNER,	#  8
  curses.ACS_URCORNER,	#  9
  curses.ACS_LLCORNER,	# 10
  curses.ACS_LRCORNER,	# 11
  curses.ACS_CKBOARD,	# 12
		   'M'	# 13 #TODO add monster types
  ]

  curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(8, curses.COLOR_GREEN, curses.COLOR_RED)
#  curses.init_pair(9, curses.COLOR_YELLOW, curses.COLOR_MAGENTA)
"""  colors = [
  curses.color_pair(0),	#  0
  curses.color_pair(1),	#  1
  curses.color_pair(2),	#  2
  curses.color_pair(3),	#  3
  curses.color_pair(4),	#  4
  curses.color_pair(5),	#  5
  curses.color_pair(6),	#  6
  curses.color_pair(7),	#  7
  curses.color_pair(8),	#  8
  curses.color_pair(9),	#  9
  curses.color_pair(0),	# 10
  curses.color_pair(1),	# 11
  curses.color_pair(2),	# 12
  curses.color_pair(3),	# 13
  ]"""

def getDisplayChar(i): return chars[i]
#def getDisplayCharColor(i): return colors[i]

solid = [5,6,7,8,9,10,11] #cannot move through
opaque = [5,6,7,8,9,10,11,12] # cannot see through
inverted = []

logfile = 'quest_log.txt' #where the log output will appear
logMinPriority = 0 #used to prioritize logged info (low numbers are low priority)
logContents = []
repeated = 0

#writes a line to the logfile
def log(priority, text, value=''):
  global repeated
  if priority < logMinPriority: return #if message of this priority have been hidden, return
  text = str(text)
  if not value == '': text = text + ': ' + str(value)
  text = text + '\n'
  if len(logContents) > 1:
    if text == logContents[-2] and (text == logContents[-1] or repeated>0):
      logContents.pop()
      repeated +=1
      text = 'Previous message repeated '+str(repeated)+' more times.\n\n'
    else: repeated = 1

  logContents.append(text)
  with open(logfile, 'w') as file: file.writelines(logContents)

log(1000, '==== Quest Log File ====') #TODO rename the game

#restricts the imput to be between min and max
def limit(value, minval, maxval): return min(maxval, max(minval, value))

def randSkip(min, max):	return random.choice(range(min, max, 2))

def doublerange(xlen, ylen=0):
  if ylen == 0 and xlen.__class__ in [tuple, list]:
    return doublerange(xlen[0], xlen[1])
  return itertools.product(range(xlen), range(ylen))

class Item: #TODO add items
  'Contains one item and all its properties.'
  def __init__(self, itemID):
    self.setItem(itemID)
  def setID(self, itemID):
    self.itemID = itemID
  def getID(self):
    return self.itemID

class Tile:
  'Contains the terrain and a list of items.'
  def __init__(self, terrainID, color, items, shown): #TODO make terrain an item and add item colors
    self.terrainID = terrainID
    self.color = color
    self.items = items
    self.shown = shown
  #terrain is the material that is seen
  def setTerrain(self, terrainID): self.terrainID = terrainID
  def getTerrain(self):            return self.terrainID
  def setColor(self, color):       self.color = color
  def getColor(self):              return self.color

  def setItems(self, items):	self.items = items
  def getItems(self):		return self.items
  def addItem(self, item):	self.items.append(item)
  def popItem(self):		return self.items.pop()
  def show(self):		self.shown = True
  def hide(self):		self.shown = False
  def isShown(self):		return self.shown #TODO this needs to be on each creature

#Doesn't have to be doors - could also be walls, cells, or anything with 4 directions
class Doors:
  'Stores info about which of the 4 directions are active'
  def __init__(self, left, right, top, bottom):
    self.doors = [left, right, top, bottom]
  def getIndex(self, i):	return self.doors[i]
  def setIndex(self, i, value):	self.doors[i] = value
  def getLeft(self):		return self.doors[0]
  def getRight(self):		return self.doors[1]
  def getTop(self):		return self.doors[2]
  def getBottom(self):		return self.doors[3]
  def setLeft(self, left):	self.doors[0] = left
  def setRight(self, right):	self.doors[1] = right
  def setTop(self, top):	self.doors[2] = top
  def setBottom(self, bottom):	self.doors[3] = bottom
  def getInverse(self): #swap left with right and top with bottom
    return Doors(self.doors[1], self.doors[0], self.doors[3], self.doors[2])
  def add(self, doors):
    self.doors = [mine or add for mine, add in zip(self.doors, doors.doors)]

class Room:
  'Contains one room of a level and all the objects in it.'
  def __init__(self, width, length): #create a new room
    log(6, '      ===== new Room '+str(width)+'x'+str(length)+' =====')
    self.doors = Doors(False, False, False, False)
    #minimum dimensions are 3x3
    if width<3: width = 3
    if length<3: length = 3
    #store the width and length
    self.width = width
    self.length = length
    #template defines the smallest room
    template = [
    [8,6,9],
    [7,1,7],
    [10,6,11]
    ]
    #construct the room row by row
    self.room = []
    for y in range(self.length):
      row = []
      for x in range(self.width):
        #use template to find out which terrain to use
        templateX = (x>0)+(x==self.width-1)
        templateY = (y>0)+(y==self.length-1)
        terrainID = template[templateY][templateX]
        row.append(Tile(terrainID, 0, [], True))
      self.room.append(row)
  def fillIn(self, char):
    for x, y in doublerange(self.width, self.length):
      self.getTile(x, y).setTerrain(char)
  def getWL(self): return self.width, self.length  #return the dimensions
  def getTile(self, x, y): return self.room[y][x] # get a Tile object at specified coordinates
  def addDoors(self, doors):
    self.doors.add(doors) #combine the current doors and the new doors info
    for x, y in doublerange(self.width, self.length): #add the doors to the actual room
      if doors.getLeft()   and abs(y-(self.length-1)/2.0)<1 and x==0 \
      or doors.getRight()  and abs(y-(self.length-1)/2.0)<1 and x==self.width-1\
      or doors.getTop()    and abs(x-(self.width -1)/2.0)<1 and y==0 \
      or doors.getBottom() and abs(x-(self.width -1)/2.0)<1 and y==self.length-1:
        tile = self.getTile(x, y)
        tile.setTerrain(DOOR_ID)
        tile.setColor(DOOR_COLOR)
  def populate(self, density, char): #fill some tiles of a room randomly using density
    for x, y in doublerange(self.width, self.length):
      tile = self.getTile(x, y)
      if tile.getTerrain() == 1 and random.random() < density: tile.setTerrain(char)
  def getDoors(self): return self.doors
  def getVisibleWalls(self): #which walls have been fully explored
    shown = Doors(1, 1, 1, 1)
    for x in range(self.width): #top row
      topTile = self.room[0][x] #get the tile
      if not topTile.isShown(): shown.setTop(False) #if the tile is hidden, the wall is considered not visible
      elif topTile.getTerrain()==DOOR_ID: shown.setTop(True); break 
      #otherwise if the wall has a door, the wall is visible and it overrides hidden tiles

    for x in range(self.width): # bottom row
      bottomTile = self.room[self.length-1][x]
      if not bottomTile.isShown(): shown.setBottom(False)
      elif bottomTile.getTerrain()==DOOR_ID: shown.setBottom(True); break

    for y in range(self.length): #left row
      leftTile = self.room[y][0]
      if not leftTile.isShown(): shown.setLeft(False)
      elif leftTile.getTerrain()==DOOR_ID: shown.setLeft(True); break

    for y in range(self.length): # right row
      rightTile = self.room[y][self.width-1]
      if not rightTile.isShown(): shown.setRight(False)
      elif rightTile.getTerrain()==DOOR_ID: shown.setRight(True); break

    return shown
  def invert(self):
    for y in range(self.length):
      for x in range(self.width):
        self.getTile(x, y).hide()

class Miniroom:
  def __init__(self, shown, middle, doors, visible):
    self.shown = shown
    self.middle = middle
    self.doors = doors #openings in the wall
    self.visible = visible #visible walls
  def isShown(self):		return self.shown
  def getMiddle(self):		return self.middle
  def setMiddle(self, middle):	self.middle = middle
  def getDoors(self):		return self.doors
  def getVisibleWalls(self):	return self.visible

class Minimap: #2-D list of miniRooms
  def __init__(self, minimap): self.minimap = minimap
  def getMiniroom(self, x, y): return self.minimap[y][x]

#TODO level editor
class Level:
  'Contains a 2-D list of rooms'
  def __init__(self, type, name, width, length, roomWidth, roomLength):
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
        room = Room(roomWidth, roomLength)
        row.append(room)
      self.level.append(row)
  def getName(self):		return self.name
  def setName(self, name):	self.name = name
  def getWL(self):		return self.width, self.length #return the dimensions
  def getRoom(self, x, y):	return self.level[y][x]
  def checkForConnection(self, minimap, x, y, fill, lookFor): #used to see if the stairs are connected
    miniroom = minimap.getMiniroom(x, y)
    if miniroom.getMiddle() == fill: return False
    if miniroom.getMiddle() == lookFor: return True
    miniroom.setMiddle(fill)
    doors = miniroom.getDoors()
    if doors.getLeft():
      if self.checkForConnection(minimap, x-1, y, fill, lookFor): return True
    if doors.getRight():
      if self.checkForConnection(minimap, x+1, y, fill, lookFor): return True
    if doors.getTop():
      if self.checkForConnection(minimap, x, y-1, fill, lookFor): return True
    if doors.getBottom():
      if self.checkForConnection(minimap, x, y+1, fill, lookFor): return True
    return False
  def addStairs(self): #adds both up and down stairs to the level
    upX = upY = downX = downY = 0
    log(4, "    min Stair Distance", (self.width**2+self.length**2)/4.0)
    while (upX-downX)**2+(upY-downY)**2 < (self.width**2+self.length**2)/4.0:
      log(4, "    Stair Distance", (upX-downX)**2+(upY-downY)**2)
      upX = random.randrange(self.width)
      upY = random.randrange(self.length)
      downX = random.randrange(self.width)
      downY = random.randrange(self.length)
    log(4, "    Final Stair Distance", (upX-downX)**2+(upY-downY)**2)

    upRoom = self.getRoom(upX, upY)
    downRoom = self.getRoom(downX, downY)
    upWidth, upLength = upRoom.getWL()
    downWidth, downLength = downRoom.getWL()
    upRoom.getTile(int(upWidth/2), int(upLength/2)).setTerrain(UP_STAIRS_ID)
    downRoom.getTile(int(downWidth/2), int(downLength/2)).setTerrain(DOWN_STAIRS_ID)
    connected = False
    while not connected:
      doors = Doors(False, False, False, False)
      i = random.randrange(4)
      x = random.randrange(self.width)
      y = random.randrange(self.length)
      x2=x
      y2=y
      if i==0:
        x2-=1
        doors.setLeft(True)
      elif i==1:
        x2+=1
        doors.setRight(True)
      elif i==2:
        y2-=1
        doors.setTop(True)
      elif i==3:
        y2+=1
        doors.setBottom(True)
      doors2 = doors.getInverse()
      if x2>=0 and x2<self.width and y2>=0 and y2<self.length:
        self.getRoom(x, y).addDoors(doors)
        self.getRoom(x2, y2).addDoors(doors2)
        minimap = self.getMinimap()
        for x, y in doublerange(self.width, self.length): #TODO make this more efficient
          minimap.getMiniroom(x, y).setMiddle(0)
        minimap.getMiniroom(downX, downY).setMiddle(2)
        connected = self.checkForConnection(minimap, upX, upY, 1, 2)

    minimap = self.getMinimap()
    for x, y in doublerange(self.width, self.length):
      minimap.getMiniroom(x, y).setMiddle(0)
    self.fill(minimap, upX, upY, 1)
    #TODO remove rows and columns of dead rooms or add hallways into them
    for x, y in doublerange(self.width, self.length):
      if minimap.getMiniroom(x, y).getMiddle() == 0:
        self.getRoom(x, y).fillIn(BLOCK_ID)

    log(4, '    Level layout:')
    for y in range(self.length):
      line = ''
      for x in range(self.width):
        if (x==upX and y==upY) or (x==downX and y==downY):
          line += '2'
        else:
          line += str(minimap.getMiniroom(x,y).getMiddle())
      log(4,'    '+line+'    y:'+str(y))
    log(4, '')

  def fill(self, minimap, x, y, fill): #used to see if the stairs are connected
    miniroom = minimap.getMiniroom(x, y)
    if miniroom.getMiddle() == fill: return
    miniroom.setMiddle(fill)
    doors = miniroom.getDoors()
    if doors.getLeft():   self.fill(minimap, x-1, y, fill)
    if doors.getRight():  self.fill(minimap, x+1, y, fill)
    if doors.getTop():    self.fill(minimap, x, y-1, fill)
    if doors.getBottom(): self.fill(minimap, x, y+1, fill)

  def findChar(self, char):
    for x, y in doublerange(self.width, self.length):
      room = self.getRoom(x, y)
      roomWidth, roomLength = room.getWL()
      for x2, y2 in doublerange(roomWidth, roomLength):
        if room.getTile(x2, y2).getTerrain()==char: return x, y, x2, y2
    return 0,0,0,0
  def invert(self):
    for x, y in doublerange(self.width, self.length):
      self.getRoom(x, y).invert()
  def getMinimap(self):
    minimap = []
    for y in range(self.length):
      row = []
      for x in range(self.width):
        shown = False
        room = self.getRoom(x, y)
        roomWidth, roomLength = room.getWL()
        for x2, y2 in doublerange(roomWidth, roomLength):
          if room.getTile(x2, y2).isShown(): shown = True
        middle = 0
        for x2, y2 in doublerange(roomWidth, roomLength):
          terrain = room.getTile(x2, y2).getTerrain()
          if terrain == UP_STAIRS_ID \
          or terrain == DOWN_STAIRS_ID: middle = terrain
        doors = room.getDoors()
        visible = room.getVisibleWalls()
        row.append(Miniroom(shown, middle, doors, visible))
      minimap.append(row)
    return Minimap(minimap)
  def loadRoom(self, levelX, levelY):
    room = self.getRoom(levelX, levelY)
    roomWidth, roomLength = room.getWL()
    return room, roomWidth, roomLength

class Levelset:
  def __init__(self, levels):
    self.levels = levels
    self.height = len(levels)
    log(8, '  ===== new Levelset height: '+str(self.height)+' =====')    
  def getHeight(self):	return self.height
  def getLevel(self, i):return self.levels[i]
  def getStartingLocation(self):
    level = self.getLevel(0)
    levelX, levelY, roomX, roomY = level.findChar(UP_STAIRS_ID)
    location = Location(0, levelX, levelY, roomX, roomY)
    return location

def randomLevel(name):
  levelWidth = random.randint(4,6)
  levelheight = random.randint(3,5)
  roomWidth = randSkip(7,17)
  roomLength = randSkip(7,15)
  level = Level(DEFAULT_LEVEL, name, levelWidth, levelheight, roomWidth, roomLength)
  level.addStairs()
  level.invert()
  return level

def randomLevelset(height):
  log(6, '  ===== creating '+str(height)+' random levels =====')
  levels = []
  for i in range(height):
    level = randomLevel('DLVL '+str(i))
    levels.append(level)
  return Levelset(levels)

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
  def move(self, dx, dy, creatures, level):
    if dx==0 and dy==0: return False, None
    levelWidth, levelLength = level.getWL()
    room = level.getRoom(self.levelX, self.levelY)
    roomWidth, roomLength = room.getWL()
    x2=self.roomX+dx
    y2=self.roomY+dy
    if x2<-1 or x2>roomWidth or \
    y2<-1 or y2>roomLength:
      return False, None
    terrain = room.getTile(self.roomX, self.roomY).getTerrain()
    newTerrain = room.getTile(limit(x2, 0, roomWidth-1), limit(y2, 0, roomLength-1)).getTerrain()
    if newTerrain in solid:
#     if self.getName() != 'player': #uncomment to walk through walls (doesn't work now)
      return False, None
    enemy = creatures.findAt(self.z, self.levelX, self.levelY, x2, y2)
    if enemy != None: #if there is an enemy
      return True, enemy #return it

    #if moving diagonally and standing on a door or attempting to move on to one
    if dx != 0 and dy != 0 and DOOR_ID in [terrain, newTerrain]:
      return False, None
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
    return True, None

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
  def act(self):
    self.healthTimer -= 1
    if self.healthTimer < 1:
      self.healthTimer = 10
      self.changeHealth(1)

#TODO add closed doors as a terrain or entity/creature
#TODO add entities class (or use creatures for it)
class Creature:
  def __init__(self, levelset, location, stats):
    self.levelset = levelset
    self.location = location
    self.stats = stats
  def getStats(self): return self.stats
  def getLocation(self): return self.location
  def getName(self):  return 'creature'
  def act(self):
    self.stats.act()
    return True
  def loadLevel(self, stairsChar):
    level = self.levelset.getLevel(self.location.getZ())
    levelX, levelY, roomX, roomY = level.findChar(stairsChar)

    self.location.setLevelXY(levelX, levelY)
    self.location.setRoomXY(roomX, roomY)
  def goUp(self):
    if self.location.getZ() <= 0: return False
    self.location.changeZ(-1)
    log(4, getDisplayChar(self.getChar())+' went up a dungeon level. z', self.location.getZ())
    self.loadLevel(DOWN_STAIRS_ID)
    return True
  def goDown(self):
    if self.location.getZ() >= self.levelset.getHeight()-1: return False
    self.location.changeZ(1)
    log(4, getDisplayChar(self.getChar())+' went down a dungeon level. z', self.location.getZ())
    self.loadLevel(UP_STAIRS_ID)
    return True
  def getLevel(self):  return self.levelset.getLevel(self.location.getZ())
  def getRoom(self):
    levelX, levelY = self.location.getLevelXY()
    return self.getLevel().getRoom(levelX, levelY)
  def wander(self, creatures):
    return self.move(random.randint(-1,1),random.randint(-1,1), creatures)
  def move(self, dx, dy, creatures):
    moved, enemy = self.location.move(dx, dy, creatures, self.getLevel())
    if enemy != None:
      #if self.attack(enemy): return True
      enemy.getStats().takeDamage(1) #TODO different amounts of damage, only attack enemies
    return moved

class Monster(Creature):
  def getChar(self): return MONSTER_ID
  def getName(self): return 'monster'
  def act(self, creatures):
    #TODO remember player location and navigate there even if it is in a different room
    self.stats.act()
    player = creatures.getPlayer()
    x1, y1 = self.location.getLevelXY()
    x2, y2 = player.getLocation().getLevelXY()
    if x1 != x2 or y1 != y2:
      for i in range(10): 
        if self.wander(creatures): return True
      return True;
    x1, y1 = self.location.getRoomXY()
    x2, y2 = player.getLocation().getRoomXY()
    dx = dy = 0
    if x2>x1: dx=1
    if x2<x1: dx=-1
    if y2>y1: dy=1
    if y2<y1: dy=-1
#    log(2, 'dx', dx)
#    log(2, 'dy', dy)
    roomX, roomY = self.location.getRoomXY()
    terrain = self.getRoom().getTile(roomX, roomY).getTerrain()
    if terrain == UP_STAIRS_ID: self.goUp()
    elif terrain == DOWN_STAIRS_ID: self.goDown()
    else:self.move(dx, dy, creatures)
    return True

class Player(Creature):
  def getChar(self):	return 2
  def getName(self):	return 'player'
  def raycast(self): 
    startX, startY = self.location.getRoomXY()
#    log('======raycast at ('+str(startX)+', '+str(startY)+')=======')
    room = self.getRoom()
    roomWidth, roomLength = room.getWL()
    direction = 0
    room.getTile(startX, startY).show()
    while direction <= 2.1*math.pi:
      x=startX
      y=startY
      walls = 0
      distance = 0
      while walls < 1 and distance < 15:
        distance += 1
        x+=math.cos(direction)
        y+=math.sin(direction)
        xint = int(x+.5)
        yint = int(y+.5)
        if xint > roomWidth-1 or yint > roomLength-1 or xint < 0 or yint < 0:
          walls += 1
        else:
          tile = room.getTile(xint, yint)
          tile.show()
          char = tile.getTerrain()
          if char in opaque: walls += 1
      direction += .01*math.pi
  def act(self, creatures, key):
  #returns whether or not the player moved/took an action
    self.stats.act()
    level = self.getLevel()
    levelWidth, levelLength = level.getWL()
    room = self.getRoom()
    roomWidth, roomLength = room.getWL()
    dx = [-1, 0, 1, 1,  1,  0, -1, -1]
    dy = [ 1, 1, 1, 0, -1, -1, -1,  0]
    for i in range(8):
      if key == moveOpts[i][2]: return self.move(dx[i], dy[i], creatures) #TODO arrows/wasd double press controls

    roomX, roomY = self.location.getRoomXY()
    terrain = room.getTile(roomX, roomY).getTerrain()
    if (key == '\n' or key == '<') and terrain == UP_STAIRS_ID: return self.goUp()
    if (key == '\n' or key == '>') and terrain == DOWN_STAIRS_ID: return self.goDown()
    return False

class Creatures():
  def __init__(self, levelset, frequency, player):
    self.creatures = [player]
    self.levelset = levelset
    for z in range(levelset.getHeight()):
      level = levelset.getLevel(z)
      for levelX, levelY in doublerange(level.getWL()):
        room = level.getRoom(levelX,levelY)
        for roomX, roomY in doublerange(room.getWL()):
          tile = room.getTile(roomX,roomY)
          if not tile.getTerrain() in solid and frequency > random.random():
            self.creatures.append( Monster(levelset,Location(z,levelX,levelY,roomX,roomY), Stats(2, 3)) )
            log(4, 'Added monster.')
#            log(1, 'Added monster. z:'+str(z)+' levelXY:('+str(levelX)+','+str(levelY)+') roomXY:('+str(roomX)+','+str(roomY)+')')
  def getList(self): return self.creatures
  def getPlayer(self): return self.creatures[0]
  def getStats(self):
    stats = 'Creatures: '
    for c in self.creatures:
      stats += '['+getDisplayChar(c.getChar())+', '+c.getName()+', HP:'+str(c.getStats().getHealth())+'/'+str(c.getStats().getMaxHealth())+']'
    return stats
  def removeDead(self): # Bring out your dead!
    #rebuild the list, excluding creatures that return false for isAlive()
    self.creatures = [creature for creature in self.creatures if creature.getStats().isAlive()]
  def act(self):
    self.removeDead()
    for creature in self.creatures[1:]: #loop over a copy of creatures that excludes the 1st item (the player)
    #the copy also keeps it from messing up if one dies
      creature.act(self) #tell each creature to do its thing
      self.removeDead() #if it or any other creature died while on its turn, remove it
    return True
  def findAt(self, z, levelX, levelY, roomX, roomY):
    for creature in self.creatures:
      location = creature.getLocation()
      if location.getZ() == z:
        if location.getLevelXY() == (levelX, levelY):
          if location.getRoomXY() == (roomX, roomY):
            return creature
    return None

def display(screen, creatures):
  displayStartTime = time.time()
  player = creatures.getPlayer()
  location = player.getLocation()
  z = location.getZ()
  level = player.getLevel()
  levelX, levelY = location.getLevelXY()
  roomX, roomY = location.getRoomXY()
  room = level.getRoom(levelX, levelY)

  roomWidth, roomLength = room.getWL()
  levelWidth, levelLength = level.getWL()

  screen.clear()
#  screen.addstr(2,0,'DLVL' + str(z))
  creatureStats = creatures.getStats()
  screen.addstr(1,0,level.getName()+' HP:'+str(player.getStats().getHealth())+'/'+str(player.getStats().getMaxHealth())+' '+creatureStats, curses.A_REVERSE)

  roomDispX = levelWidth*5+3
  roomDispY = 5

#  log(5, 'width', levelWidth*5+2)
#  log(5, 'height', levelLength*3+2)

  #                       h,l,y,x
  miniWin = curses.newwin(levelLength*3+2, levelWidth*5+2, roomDispY, 0)
#  miniWin.clear()
  miniWin.border()

  minimap = level.getMinimap()

  for x, y in doublerange(levelWidth, levelLength):
    miniroom = minimap.getMiniroom(x, y)
    if miniroom.isShown():
      middle=miniroom.getMiddle()
      if x==levelX and y==levelY: middle=player.getChar()
      miniWin.addstr(2+y*3,2+x*5, '[ ]')
      miniWin.addch(2+y*3,3+x*5, getDisplayChar(middle))
      doors = miniroom.getDoors()
      visible = miniroom.getVisibleWalls()
      char = ''
      if not visible.getTop(): char = '?'
      elif doors.getTop(): char = '|'
      else: char = ' '
      miniWin.addch(1+y*3,3+x*5, char)

      if not visible.getBottom(): char = '?'
      elif doors.getBottom(): char = '|'
      else: char = ' '
      miniWin.addch(3+y*3,3+x*5, char)

      if not visible.getLeft(): char = '?'
      elif doors.getLeft(): char = '-'
      else: char = ' '
      miniWin.addch(2+y*3,1+x*5, char)

      if not visible.getRight(): char = '?'
      elif doors.getRight(): char = '-'
      else: char = ' '
      #log(5, 'x', 5+x*5)
      #log(5, 'y', 2+y*3)
      miniWin.addch(2+y*3,5+x*5, char)

  #TODO fix the room window needing 1 extra length/width (roomWidth+1)
  roomWin = curses.newwin(roomLength, roomWidth+1, roomDispY, roomDispX)
#  roomWin.border()

  for x, y in doublerange(roomWidth, roomLength):
    tile = room.getTile(x, y)
    char = tile.getTerrain()
    color = tile.getColor()
    if not tile.isShown(): char = color = 0
#    log(5, 'width', roomWidth)
#    log(5, 'length', roomLength)
#    log(5, 'x', x)
#    log(5, 'y', y)

#    roomWin.addch(y,x,getDisplayChar(char), curses.color_pair(1))
    roomWin.addch(y,x,getDisplayChar(char), curses.color_pair(color))
#    roomWin.addch(y,x,getDisplayChar(char))
  for creature in reversed(creatures.getList()):
    location = creature.getLocation()
    cz = location.getZ()
    if cz != z: continue
    clevelX, clevelY = location.getLevelXY()
    if clevelX != levelX or clevelY != levelY: continue
    roomX, roomY = location.getRoomXY()
    char = creature.getChar()
    roomWin.addch(roomY,roomX,getDisplayChar(char))

  screen.noutrefresh() #mark each screen for refresh but wait
  roomWin.noutrefresh()
  miniWin.noutrefresh()
  curses.doupdate() #refresh all screens at the same time
  screen.move(roomDispY+roomY, roomDispX+roomX)
#  log(1, 'Display time', time.time() - displayStartTime)

def optionsMenu(screen):
  quit = False
  #                   h,  l,  y, x
  win = curses.newwin(19, 27, 0, 6)
  win.clear()
  win.border()
  while not quit:
    win.addstr(1,7,'Options')
    for i in range(1,len(moveOpts)):
      y=i+3
      option = moveOpts[i]
      win.addstr(y,2,option[0])
      reverse = option[3]*curses.A_REVERSE
      if i>8:
        win.addstr(y,14,option[1], reverse)
      else:
        win.addch(y,14,option[1], reverse)
    win.addstr(y+2,4,'Press q to quit')
    key = win.getkey()
    win.refresh()

    if key=='1':
      moveOpts[9][3] = True
      moveOpts[10][3] = False
      moveOpts[11][3] = False
      for i in range(8):
        moveOpts[i][1] = ['1','2','3','6','9','8','7','4'][i]
        moveOpts[i][2] = ['1','2','3','6','9','8','7','4'][i]
    elif key=='2':
      moveOpts[9][3] = False
      moveOpts[10][3] = True
      moveOpts[11][3] = False
      for i in range(8):
        moveOpts[i][1] = ['1','v','3','>','9','^','7','<'][i]
        moveOpts[i][2] = ['1','KEY_DOWN','3','KEY_RIGHT','9','KEY_UP','7','KEY_LEFT'][i]
    elif key=='3':
      moveOpts[9][3] = False
      moveOpts[10][3] = False
      moveOpts[11][3] = True
      for i in range(8):
        moveOpts[i][1] = ['Z','X','C','D','E','W','Q','A'][i]
        moveOpts[i][2] = ['z','x','c','d','e','w','q','a'][i]
    #                enter key    spacebar
    elif key=='q' or key=='\n' or key== ' ': quit = True
  del win
  screen.clear()
  return moveOpts

def extendedCommand(screen): #TODO use curses.textpad for extended commands
  command=''
  key='#'
  while not key=='\n':
    if key=='KEY_BACKSPACE':
      command=command[:-1]
      screen.addch(0,len(command),' ')
      if command=='': return ''
    else:
      command+=key
    screen.addstr(0,0,command)
    key=screen.getkey()
  return command

#movement key options
moveOpts = [
['South-West ', '1', '1', True],
['South      ', '2', '2', True],
['South-East ', '3', '3', True],
['East       ', '6', '6', True],
['North-East ', '9', '9', True],
['North      ', '8', '8', True],
['North-West ', '7', '7', True],
['West       ', '4', '4', True],
['           ', ' ', ' ', False],
['Press 1 for', 'numpad', ' ', True],
['Press 2 for', 'arrows+1379', ' ', False],
['Press 3 for', 'QWEASDZXC', ' ', False]
]

def main(screen):
  screen.clear() #Clear terminal screen
  initializeChars()

  #good layout: level:6x3 room:13x11 or 15x11

  height = 3
  levelset = randomLevelset(height)

  stats = Stats(20, 21)
  location = levelset.getStartingLocation()
  player = Player(levelset, location, stats)

  #generate the monsters
  creatures = Creatures(levelset, 0.01, player) #0.01 is monster generation frequency
#  pickle.dump(creatures, open('quest_tmp.txt', 'w')) #TODO save game

  log(10, 'Startup time', time.time() - startTime)
  log(8, 'curses.has_colors()', curses.has_colors())
  while True:
    if not player.getStats().isAlive():
      #                   h,  l,  y, x
      win = curses.newwin(4,  17, 0, 6)
      win.border()
      win.addstr(1,4,'You Died!') #TODO improve player death method
      win.addstr(2,1,'Press q to quit')
      win.refresh()
      key = ' '
      while key != 'q': key = screen.getkey()
      return
    player.raycast()
    display(screen, creatures)
    key = screen.getkey()
    while not player.act(creatures, key):
      if key == 'o':
        optionsMenu(screen)
        display(screen, creatures)
      elif key == '#':
        command = extendedCommand(screen)
        if command=='#quit': return
        display(screen, creatures)
      key = screen.getkey()
    creatures.act()
curses.wrapper(main)



# 	NEW FEATURES:
# do the TODO's
# ssh server to play the game on
# remove rows and columns of dead rooms or add hallways into them
# creature levels
# health system - never show HP, show health level based on percentage (hurt, very hurt, etc.) or just show percentage (50% Health, 51% Health, etc.)
# have monsters follow player between rooms
# messages
# "You hear a sound to the west." telling you a monster moved there
# change Tile.isShown to be for each creature somehow
# use level types to generate different layouts
# save game
# creature types
# creature colors
# arrow keys double press controls (or wasd double press)
# town top level
# think of a better name for the game
# 
# 	INTERNAL FEATURES:
# add constants
# level editor
# add comments and log values
# 
# 	BUGS:
# fix roomWin requiring 1 extra width or height to work
# going down a floor messes up?
# 
# 	DONE:
# remove dead rooms
# generate monsters
# have monsters travel between rooms
# change " to '
# have monsters attack
# add monsters
# fix raycaster
# hide unseen doors in minimap
# fix transitions between rooms
# have player extend creature
# display dungeon level
# add special characters
# level names
# split display function into 3 windows: room, minimap, and stats
