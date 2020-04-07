#!/bin/bash
cat "$0" | tail -871 > tmp.py
chmod 755 tmp.py
#rm "$0"
exit

#!/usr/bin/python
import os, random, math, time, curses, sys, itertools, pickle

startTime = time.time()
#chars = '.#^v!Os-*:++;[???---////TT(r)?[[[]]]]?ooooo???????'

UP_STAIRS_ID = 3
DOWN_STAIRS_ID = 4

DEFAULT_LEVEL = 0
CUSTOM_LEVEL = 1
LEVEL_FROM_FILE = 2

#these are the types of terrain and items
def getDisplayChar(i):
  chars = [	   ' ',	#  0
		   '.',	#  1
		   '@',	#  2
		   '<',	#  3
		   '>',	#  4
  curses.ACS_CKBOARD,	#  5
  curses.ACS_HLINE,	#  6
  curses.ACS_VLINE,	#  7
  curses.ACS_ULCORNER,	#  8
  curses.ACS_URCORNER,	#  9
  curses.ACS_LLCORNER,	# 10
  curses.ACS_LRCORNER,	# 11
		   'M',	# 12
  ]
  return chars[i]

solid = [5,6,7,8,9,10,11] #cannot move through
opaque = [5,6,7,8,9,10,11] # cannot see through

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

log(1000, '==== Quest Log File ====')

#restricts the imput to be between min and max
def limit(value, minval, maxval):
  return min(maxval, max(minval, value))

def randSkip(min, max):
  return random.choice(range(min, max, 2))

#def rescale(a, b, x):
#  sign=0
#  if x>(a-1)/2: sign= 1
#  if x<(a-1)/2: sign=-1
#  return(2*b*x+b-a-b*sign)/(2*a)

def doublerange(xlen, ylen):
  return itertools.product(range(xlen), range(ylen))

class Item:
  'Contains one item and all its properties.'
  def __init__(self, itemID):
    self.setItem(itemID)
  def setItem(self, itemID):
    self.itemID = itemID
  def getItem(self):
    return self.itemID

class Tile:
  'Contains the terrain and a list of items.'
  def __init__(self, terrainID, items, shown):
    self.setTerrain(terrainID)
    self.setItems(items)
    self.show()
  def setTerrain(self, terrainID): #terrain is the material that is seen
    self.terrainID = terrainID
  def getTerrain(self):
    return self.terrainID
  def setItems(self, items):
    self.items = items
  def getItems(self):
    return self.items
  def addItem(self, item):
    self.items.append(item)
  def popItem(self):
    return self.items.pop()
  def show(self):
    self.shown = True
  def hide(self):
    self.shown = False
  def isShown(self):
    return self.shown

#Doesn't have to be doors - could also be walls, cells, or anything with 4 directions
class Doors:
  'Stores info about which of the 4 directions are active'
  def __init__(self, left, right, top, bottom):
    self.doors = [left, right, top, bottom]
  def getIndex(self, i):
    return self.doors[i]
  def setIndex(self, i, value):
    self.doors[i] = value
  def getLeft(self):
    return self.doors[0]
  def getRight(self):
    return self.doors[1]
  def getTop(self):
    return self.doors[2]
  def getBottom(self):
    return self.doors[3]
  def setLeft(self, left):
    self.doors[0] = left
  def setRight(self, right):
    self.doors[1] = right
  def setTop(self, top):
    self.doors[2] = top
  def setBottom(self, bottom):
    self.doors[3] = bottom
  def getInverse(self): #swap left with right and top with bottom
    return Doors(self.doors[1], self.doors[0], self.doors[3], self.doors[2])
  def add(self, doors):
    self.doors = [sd or dd for sd, dd in zip(self.doors, doors.doors)]
#    self.doors[0] = self.doors[0] or doors.doors[0]
#    self.doors[1] = self.doors[1] or doors.doors[1]
#    self.doors[2] = self.doors[2] or doors.doors[2]
#    self.doors[3] = self.doors[3] or doors.doors[3]

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
        row.append(Tile(terrainID, [], True))
      self.room.append(row)
  def getWL(self):
    #return the dimensions
    return self.width, self.length
  def getTile(self, x, y):
    return self.room[y][x] # get a Tile object at specified coordinates
  def addDoors(self, doors):
    self.doors.add(doors) #combine the current doors and the new doors info
    for x, y in doublerange(self.width, self.length): #add the doors to the actual room
      if doors.getLeft()   and abs(y-(self.length-1)/2.0)<1 and x==0 \
      or doors.getRight()  and abs(y-(self.length-1)/2.0)<1 and x==self.width-1\
      or doors.getTop()    and abs(x-(self.width -1)/2.0)<1 and y==0 \
      or doors.getBottom() and abs(x-(self.width -1)/2.0)<1 and y==self.length-1:
        self.getTile(x, y).setTerrain(1)
  def populate(self, density, char): #fill some tiles of a room randomly using density
    for x, y in doublerange(self.width, self.length):
      tile = self.getTile(x, y)
      if tile.getTerrain() == 1 and random.random() < density: tile.setTerrain(char)

  def getDoors(self):
    return self.doors
  def getVisibleWalls(self): #which walls have been fully explored
    shown = Doors(1, 1, 1, 1)
    for x in range(self.width): #top row
      topTile = self.room[0][x] #get the tile
      if not topTile.isShown(): shown.setTop(False) #if the tile is hidden, the wall is considered not visible
      elif topTile.getTerrain()==1: shown.setTop(True); break 
      #otherwise if the wall has a door, the wall is visible and it overrides hidden tiles

    for x in range(self.width): # bottom row
      bottomTile = self.room[self.length-1][x]
      if not bottomTile.isShown(): shown.setBottom(False)
      elif bottomTile.getTerrain()==1: shown.setBottom(True); break

    for y in range(self.length): #left row
      leftTile = self.room[y][0]
      if not leftTile.isShown(): shown.setLeft(False)
      elif leftTile.getTerrain()==1: shown.setLeft(True); break

    for y in range(self.length): # right row
      rightTile = self.room[y][self.width-1]
      if not rightTile.isShown(): shown.setRight(False)
      elif rightTile.getTerrain()==1: shown.setRight(True); break

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
  def isShown(self):
    return self.shown
  def getMiddle(self):
    return self.middle
  def setMiddle(self, middle):
    self.middle = middle
  def getDoors(self):
    return self.doors
  def getVisibleWalls(self):
    return self.visible

class Minimap: #2-D list of miniRooms
  def __init__(self, minimap):
    self.minimap = minimap
  def getMiniroom(self, x, y):
    return self.minimap[y][x]

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
  def getName(self):
    return self.name
  def setName(self, name):
    self.name = name
  def getWL(self):
    #return the dimensions
    return self.width, self.length
  def getRoom(self, x, y):
    return self.level[y][x]
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
    upX = random.randrange(self.width)
    upY = random.randrange(self.length)
    downX = upX
    downY = upY
    while upX==downX and upY==downY:
      downX = random.randrange(self.width)
      downY = random.randrange(self.length)
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
        for x, y in doublerange(self.width, self.length):
          minimap.getMiniroom(x, y).setMiddle(0)
        minimap.getMiniroom(downX, downY).setMiddle(2)
        connected = self.checkForConnection(minimap, upX, upY, 1, 2)
  def findStairs(self, up):
    char = DOWN_STAIRS_ID
    if up: char = UP_STAIRS_ID
    return self.findChar(char)
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
  def getHeight(self):
    return self.height
  def getLevel(self, i):
    return self.levels[i]
  def loadLevel(self, i, upStairs):
    level = self.getLevel(i)
    levelWidth, levelLength = level.getWL()
    levelX, levelY, roomX, roomY = level.findStairs(upStairs)
    room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
    return level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY

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

class Creature:
  def __init__(self, levelset, z, levelX, levelY, roomX, roomY, health): 
    self.levelset = levelset
    self.z = z
    self.setLevelXY(levelX, levelY)
    self.setRoomXY(roomX, roomY)
    self.health = health
  def getHealth(self):
    return self.health
  def takeDamage(self, amount):
    self.health -= amount
  def isAlive(self):
    return self.health > 0
  def getName(self):
    return 'creature'
  def act(self):
    return True
  def loadLevel(self, upStairs):
    level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY = self.levelset.loadLevel(self.z, upStairs)

    self.setLevelXY(levelX, levelY)
    self.setRoomXY(roomX, roomY)
  def getLevelXY(self):
    return self.levelX, self.levelY
  def setLevelXY(self, levelX, levelY):
    self.levelX = levelX
    self.levelY = levelY
  def getRoomXY(self):
    return self.roomX, self.roomY
  def setRoomXY(self, roomX, roomY):
    self.roomX = roomX
    self.roomY = roomY
  def getZ(self):
    return self.z
  def goUp(self):
    if self.z <= 0: return False
    self.z -= 1
    log(4, getDisplayChar(self.getChar())+' went up a dungeon level. z', self.z)
    self.loadLevel(False)
    return True
  def goDown(self):
    if self.z >= self.levelset.getHeight()-1: return False
    self.z += 1
    log(4, getDisplayChar(self.getChar())+' went down a dungeon level. z', self.z)
    self.loadLevel(True)
    return True
  def setZ(self, z):
    difference = z - self.z
    self.z = z
    if difference > 0: self.loadLevel(True)
    if difference < 0: self.loadLevel(False)
  def getLevel(self):
    return self.levelset.getLevel(self.z)
  def getRoom(self):
    return self.getLevel().getRoom(self.levelX, self.levelY)
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
#    creature = getCreatureAt(x2, y2)
#    if not creature == None:
#      self.attack(creature)
    if room.getTile(limit(x2, 0, roomWidth-1), limit(y2, 0, roomLength-1)).getTerrain() in solid:
      return False
    for creature in creatures:
      if creature.getZ() == self.z:
        levelX, levelY = creature.getLevelXY()
        if levelX == self.levelX and levelY == self.levelY:
          roomX, roomY = creature.getRoomXY()
          if roomX == x2 and roomY == y2:
            creature.takeDamage(1) #TODO
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

class Monster(Creature):
  def getChar(self):
    return 12
  def getName(self):
    return 'monster'
  def act(self, creatures, key):
    player = creatures[0]
    x1, y1 = self.getRoomXY()
    x2, y2 = player.getRoomXY()
    dx = dy = 0
    if x2>x1: dx=1
    if x2<x1: dx=-1
    if y2>y1: dy=1
    if y2<y1: dy=-1
#    random.randint(-1,1)
#    log(2, 'dx', dx)
#    log(2, 'dy', dy)
    terrain = self.getRoom().getTile(self.roomX, self.roomY).getTerrain()
    if terrain == UP_STAIRS_ID: self.goUp()
    elif terrain == DOWN_STAIRS_ID: self.goDown()
    else:self.move(dx, dy, creatures)
#    log(1, 'x', self.roomX)
#    log(1, 'y', self.roomY)
    return True

class Player(Creature):
  def __init__(self, levelset, z, health): 
    self.levelset = levelset
    self.z = z
    self.health = health
    self.loadLevel(True)
  def getChar(self):
    return 2
  def getName(self):
    return 'player'
  def raycast(self): 
    startX, startY = self.getRoomXY()
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
    level = self.getLevel()
    levelWidth, levelLength = level.getWL()
    room = self.getRoom()
    roomWidth, roomLength = room.getWL()
#    dx = [-1, 0, 1, 1,  1,  0, -1, -1]
#    dy = [ 1, 1, 1, 0, -1, -1, -1,  0]
#    for i in range(8):
#      if key == options[i][2]: return self.move(dx[i], dy[i], creatures)

    if key == options[0][2]: return self.move(-1, 1, creatures)
    if key == options[1][2]: return self.move( 0, 1, creatures)
    if key == options[2][2]: return self.move( 1, 1, creatures)
    if key == options[3][2]: return self.move( 1, 0, creatures)
    if key == options[4][2]: return self.move( 1,-1, creatures)
    if key == options[5][2]: return self.move( 0,-1, creatures)
    if key == options[6][2]: return self.move(-1,-1, creatures)
    if key == options[7][2]: return self.move(-1, 0, creatures)

    terrain = room.getTile(self.roomX, self.roomY).getTerrain()
    if (key == '\n' or key == '<') and terrain == UP_STAIRS_ID: return self.goUp()
    if (key == '\n' or key == '>') and terrain == DOWN_STAIRS_ID: return self.goDown()
    return False

def display(screen, creatures): #room, roomX, roomY, level, levelX, levelY):
  displayStartTime = time.time()
  player = creatures[0]
  z = player.getZ()
  level = player.getLevel()
  levelX, levelY = player.getLevelXY()
  roomX, roomY = player.getRoomXY()
  room = level.getRoom(levelX, levelY)

  roomWidth, roomLength = room.getWL()
  levelWidth, levelLength = level.getWL()

  screen.clear()
#  screen.addstr(1,0,'Stats', curses.A_REVERSE)
#  screen.addstr(2,0,'DLVL' + str(z))
  creatureStats = " creatures: "
  for creature in creatures:
    creatureStats += "["+getDisplayChar(creature.getChar())+", "+creature.getName()+", HP:"+str(creature.getHealth())+"]"
  screen.addstr(1,0,level.getName()+" HP:"+str(player.getHealth())+creatureStats, curses.A_REVERSE)

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

      #if doors.getTop() and y>0: miniWin.addch(roomDispY-1+y*3,3+x*5, '|')
      #if doors.getBottom() and y<levelLength-1: miniWin.addch(roomDispY+1+y*3,3+x*5, '|')
      #if doors.getLeft() and x>0: miniWin.addch(roomDispY+y*3,1+x*5, '-')
      #if doors.getRight() and x<levelWidth-1: miniWin.addch(roomDispY+y*3,5+x*5, '-')

  roomWin = curses.newwin(roomLength, roomWidth+1, roomDispY, roomDispX)
#  roomWin.border()

  for x, y in doublerange(roomWidth, roomLength):
    tile = room.getTile(x, y)
    char = tile.getTerrain()
    if not tile.isShown(): char = 0
#    log(5, 'width', roomWidth)
#    log(5, 'length', roomLength)
#    log(5, 'x', x)
#    log(5, 'y', y)
    roomWin.addch(y,x,getDisplayChar(char))
  for creature in reversed(creatures):
    cz = creature.getZ()
    if cz != z: continue
    clevelX, clevelY = creature.getLevelXY()
    if clevelX != levelX or clevelY != levelY: continue
    roomX, roomY = creature.getRoomXY()
    char = creature.getChar()
    roomWin.addch(roomY,roomX,getDisplayChar(char))

  screen.noutrefresh() #mark each screen for refresh but wait
  roomWin.noutrefresh()
  miniWin.noutrefresh()
  curses.doupdate() #refresh all screens at the same time
  screen.move(roomDispY+roomY, roomDispX+roomX)
#  log(1, 'Display time', time.time() - displayStartTime)

def optionsMenu(screen):
#  global options
  quit = False
  #                   h,  l,  y, x
  win = curses.newwin(19, 27, 0, 6)
  win.clear()
  win.border()
  while not quit:
    win.addstr(1,7,'Options')
    for i in range(1,len(options)):
      y=i+3
      option = options[i]
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
      options[9][3] = True
      options[10][3] = False
      options[11][3] = False
      for i in range(8):
        options[i][1] = ['1','2','3','6','9','8','7','4'][i]
        options[i][2] = ['1','2','3','6','9','8','7','4'][i]
    elif key=='2':
      options[9][3] = False
      options[10][3] = True
      options[11][3] = False
      for i in range(8):
        options[i][1] = ['1','v','3','>','9','^','7','<'][i]
        options[i][2] = ['1','KEY_DOWN','3','KEY_RIGHT','9','KEY_UP','7','KEY_LEFT'][i]
    elif key=='3':
      options[9][3] = False
      options[10][3] = False
      options[11][3] = True
      for i in range(8):
        options[i][1] = ['Z','X','C','D','E','W','Q','A'][i]
        options[i][2] = ['z','x','c','d','e','w','q','a'][i]
    #                enter key    spacebar
    elif key=='q' or key=='\n' or key== ' ': quit = True
  del win
  screen.clear()
  return options

def extendedCommand(screen):
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



#key = ' '

#movement key options
options = [
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

#  global key
  
  #good layout: level:6x3 room:13x11 or 15x11

  height = 3
  levelset = randomLevelset(height)

  z = 0
  health = 20
  player = Player(levelset, z, health)

#  def __init__(self, levelset, z, levelX, levelY, roomX, roomY): 
  creatures = [Monster(levelset, 0, 1, 1, 2, 2, 10)] #last is health
#  creatures = generateMonsters(levelset, 0.05)
  creatures.insert(0, player)
#  pickle.dump(creatures, open('quest_tmp.txt', 'w'))

  log(10, 'Startup time', time.time() - startTime)
  while True:
    if not player.isAlive():
      #                   h,  l,  y, x
      win = curses.newwin(4,  17, 0, 6)
      win.border()
      win.addstr(1,4,'You Died!') #TODO
      win.addstr(2,1,'Press q to quit')
      win.refresh()
      key = ' '
      while key != 'q': key = screen.getkey()
      return
    player.raycast()
    display(screen, creatures)
    key = screen.getkey()
    for creature in creatures[:]: #loop over a copy of creatures so it will not mess up if one dies
#      log(5, creature.getName()+"'s turn")
#      if creature == player: #.getName() == 'player':
      while not creature.act(creatures, key):
        if key == 'o':
          optionsMenu(screen)
          display(screen, creatures)
        elif key == '#':
          command = extendedCommand(screen)
          if command=='#quit': return
          display(screen, creatures)
        key = screen.getkey()
      creatures = [creature for creature in creatures if creature.isAlive()]
curses.wrapper(main)





# 	NEW FEATURES:
# health system
# generate monsters
# have monsters travel between rooms
# have monsters follow player between rooms
# change Tile.isShown to be for each creature somehow
# use level types to generate different layouts
# save game
# creature colors
# arrow keys double press controls (or wasd double press)
# town top level
# 
# 	INTERNAL FEATURES:
# level editor
# add comments and log values
# 
# 	BUGS:
# fix roomWin requiring 1 extra width or height to work
# going down a floor messes up?
# 
# 	DONE:
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
