#!/usr/bin/python
VERSION = '0.5.1'
def isCompatible(version):
  return version in (VERSION)

import os

LOG_PRIORITY = 0 #used to prioritize logged info (low numbers are low priority)
ROOT_DIR = os.path.join('~', '.quest') #root dir at /home/user/.quest/
#ROOT_DIR = '~/.quest'
SAVE_GAME_DIR = 'save' #where the games will be saved (relative to ROOT_DIR)
LOG_FILE = 'log.txt' #where the log output will appear (relative to ROOT_DIR)

import random, math, time, curses, sys, itertools, gzip, signal, collections
try:
  import cPickle as pickle #cPickle is faster than pickle
  cPickleFound = True
except:
  import pickle #if cPickle does not exist, use pickle
  cPickleFound = False

#TODO ssh server to play the game on
#TODO messages
#TODO "You hear a sound to the west." telling you a monster moved there
#TODO level editor

ROOT_DIR = os.path.expanduser(ROOT_DIR) #Expand the ~ in ROOT_DIR to /home/user/
SAVE_GAME_DIR = os.path.join(ROOT_DIR, SAVE_GAME_DIR) #find the actual path to SAVE_GAME_DIR and LOG_FILE
LOG_FILE = os.path.join(ROOT_DIR, LOG_FILE)
logContents = [] #empty log
repeated = 1 #how many times the last log entry was repeated


#TODO import logging instead of making my own
#writes a line to the logfile
def log(priority, text, value=''):
  global repeated
  if priority < LOG_PRIORITY: #if message of this priority have been hidden, return
    return
  text = str(text)
  if not value == '':
    text = text + ': ' + str(value)
  text = text + '\n'
  if len(logContents) > 1:
    if text == logContents[-2] and (text == logContents[-1] or repeated > 1):
      logContents.pop()
      repeated += 1
      text = 'Previous message repeated ' + str(repeated) + ' more times.\n\n'
    else:
      repeated = 1
  logContents.append(text)
  with open(LOG_FILE, 'w') as file:
    file.writelines(logContents)


#these are the ID numbers for different items and terrain
UP_STAIRS_ID = 3
DOWN_STAIRS_ID = 4
PLAYER_ID = 2
BLOCK_ID = 5
DOOR_ID = 12
CLOSED_DOOR_ID = 77
LOCKED_DOOR_ID = 78

ALPHABET_OFFSET = 13

DOOR_COLOR = 20
STAIRS_COLOR = 15
PLAYER_COLOR = 14

NO_DOOR = 0
OPEN_DOOR = 1
CLOSED_DOOR = 2
LOCKED_DOOR = 3

def randDoorState():
  return random,randint(0, 3)

#TODO use level types to generate different layouts
RANDOM_LEVEL = 0
CUSTOM_LEVEL = 1
LEVEL_FROM_FILE = 2 #TODO town level at the top

healthColors = (9, 10, 11, 12, 13)
solid = set([5, 6, 7, 8, 9, 10, 11, 73, 74, 75, 76, 77]) #cannot move through
opaque = set([5, 6, 7, 8, 9, 10, 11, 12, 73, 74, 75, 76, 77]) # cannot see through

#TODO creature level
MonstCfg = collections.namedtuple('MonsterConfig', ('freq', 'exp', 'ID', 'color', 'HP', 'name'))

monsters = (
MonstCfg(  9,  1, 14, 14,  2, 'bat'), #0
MonstCfg(  8,  1, 31, 16,  7, 'snake'), #1
MonstCfg(  1,  1, 42, 18, 30, 'dragon'), #2
MonstCfg(  7,  1, 31, 17,  5, 'spider'), #3
MonstCfg(  6,  1, 64, 16,  3, 'zombie'), #4
MonstCfg( 10,  1, 26, 20,  1, 'newt'), #5
MonstCfg(  4,  1, 57, 19, 10, 'skeleton'), #6
MonstCfg(  5,  1, 40, 20, 14, 'owlbear') #7
)

ItemCfg = collections.namedtuple('ItemConfig', ('freq', 'ID', 'color', 'name'))

items = (
ItemCfg(  1, 65, 14, 'sword'), #0
ItemCfg(  1, 66, 15, 'map'), #1
ItemCfg(  1, 67, 16, 'shield'), #2
ItemCfg( 10, 68, 17, 'rock'), #3
ItemCfg(  1, 69, 18, 'lamp'), #4
ItemCfg(  1, 70, 19, 'boomerang'), #5
ItemCfg(  1, 71, 20, 'medit'), #6
ItemCfg(  1, 72, 14, 'rope') #7
)


def charsInit():  #chars = '.#^!-*:++;[???---////()?[[[]]]]'
  global chars, monsterGen, itemGen
  #these are the types of terrain and items

  chars = (
' ',	#  0 empty
'.',	#  1 floor
'@',	#  2 player
'<',	#  3 up stairs
'>',	#  4 down stairs
curses.ACS_BLOCK,	#  5 filled in
curses.ACS_HLINE,	#  6 \
curses.ACS_VLINE,	#  7 |
curses.ACS_ULCORNER,	#  8 | these are used for
curses.ACS_URCORNER,	#  9 | room borders
curses.ACS_LLCORNER,	# 10 |
curses.ACS_LRCORNER,	# 11 /
curses.ACS_CKBOARD,	# 12 door
# 13  14  15  16  17  18  19  20  21  22  23  24  25  26  27  28  29  30  31  32  33  34  35  36  37  38
  'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
# 39  40  41  42  43  44  45  46  47  48  49  50  51  52  53  54  55  56  57  58  59  60  61  62  63  64
  'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
'/',	# 65 sword
'~',	# 66 map
'[',	# 67 shield
'*',	# 68 rock
'(',	# 69 lamp
'(',	# 70 boomerang
'+',	# 71 medkit
'&',	# 72 rope
curses.ACS_TTEE,	# 73 #TODO substitute tees with corners of not completely visible
curses.ACS_RTEE,	# 74
curses.ACS_BTEE,	# 75
curses.ACS_LTEE,	# 76
curses.ACS_DIAMOND,	# 77 closed door
curses.ACS_DIAMOND	# 78 locked door
  )

  #color combinaions of foreground, background
  #first the health colors
  curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_RED)
  curses.init_pair(10, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(12, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(13, curses.COLOR_WHITE, curses.COLOR_GREEN)

  #then the colors for the monsters and items
  curses.init_pair(14, curses.COLOR_BLUE, curses.COLOR_BLACK)
  curses.init_pair(15, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(16, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(17, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.init_pair(18, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(19, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(20, curses.COLOR_YELLOW, curses.COLOR_BLACK)

  itemGen = []
  for type in range(len(items)):
    item = items[type]
    freq = item.freq
    for i in range(freq): itemGen.append(type)

  monsterGen = []
  for type in range(len(monsters)):
    monster = monsters[type]
    freq = monster.freq
    for i in range(freq): monsterGen.append(type)


def randMonster(levelset, pos, z):
  monster = Monster(levelset, pos, 0)
  monster.init(random.choice(monsterGen), z)
  return monster


def randItem():
  return Item(random.choice(itemGen))


#implementation of xrange that works in python 2 and 3 (it speeds up the range function in python 2)
def range(start, stop=None, step=1):
  if stop is None:
    stop = start
    start = 0
  while start < stop:
    yield start
    start += step


def doublerange(xlen, ylen=0):
  if ylen == 0 and xlen.__class__ in [tuple, list]:
    return doublerange(xlen[0], xlen[1])
  return itertools.product(range(xlen), range(ylen))


def randBool():
  return bool(random.getrandbits(1))


#restricts x to be between min and max
def limit(x, low, high):
  return min(high, max(low, x))


#random even/odd numbers (depending on whether min is even or odd)
def randSkip(start, stop):
  return random.choice(list(range(start, stop, 2)))


def newPos(z, levelX, levelY, roomX, roomY):
  return {'z': z, 'levelX': levelX, 'levelY': levelY, 'roomX': roomX, 'roomY': roomY}


class Item: #TODO add items
  'Contains one item and all its properties.'
  def __init__(self, type):
      me = items[type]
      self.ID = me.ID
      self.color = me.color
      self.name = me.name
#TODO add item properties

class Tile:
  'Contains the terrain and a list of items.'
  def __init__(self, ID, color, items, shown):
    self.ID = ID  #ID and color are the terrain, which is the material that is seen
    self.color = color
    self.items = items
    self.shown = shown
  def getTopID(self):
    if len(self.items) == 0: return self.ID
    return self.items[-1].ID
  def getTopColor(self):
    if len(self.items) == 0: return self.color
    return self.items[-1].color

NORTH = TOP_RIGHT = 0
EAST = BOTTOM_RIGHT = 1
SOUTH = TOP_LEFT = 2
WEST = BOTTOM_LEFT = 3

def newCards(v):
  return (v, v, v, v)
def randCards():
  return tuple(randBool() for i in range(4))
def randCornerCards(chance):
  if random.random() < chance:
    return tuple(randBool() for i in range(4))
  else:
    return newCards(False)
def flipCard(c): #swap north with south and east with west
  return (c[SOUTH], c[WEST], c[NORTH], c[EAST])
def addCards(c1, c2):
  return tuple(v2 if v2 else v1 for v1, v2 in zip(c1, c2))
  #v2, the new value, gets priority if it is not 0

defaultSmallTemplate = ( #template defines the smallest room
    ( 8, 6, 9),
    ( 7, 1, 7),
    (10, 6,11))

BL = BLOCK_ID
filledCornersTemplate = (
    (BL,BL, 8, 6, 9,BL,BL),
    (BL,BL, 7, 1, 7,BL,BL),
    ( 8, 6,11, 1,10, 6, 9),
    ( 7, 1, 1, 1, 1, 1, 7),
    (10, 6, 9, 1, 8, 6,11),
    (BL,BL, 7, 1, 7,BL,BL),
    (BL,BL,10, 6,11,BL,BL))

hollowCornersTemplate = (
    ( 8, 6,73, 6,73, 6, 9),
    ( 7, 1, 7, 1, 7, 1, 7),
    (76, 6,11, 1,10, 6,74),
    ( 7, 1, 1, 1, 1, 1, 7),
    (76, 6, 9, 1, 8, 6,74),
    ( 7, 1, 7, 1, 7, 1, 7),
    (10, 6,75, 6,75, 6,11))

#TODO add room types
#TODO change room, level, and minimap to flattened lists (if that would be faster)
class Room:
  'Contains one room of a level and all the objects in it.'
  def __init__(self, width, length, corners, hW, smallTemplate, cornersTemplate): #create a new room
    #hW = hallwayWidth
    self.doors = newCards(NO_DOOR)
    if width < 3: width = 3 #minimum dimensions are 3x3
    if length < 3: length = 3
    self.width = width #store the width and length
    self.length = length
    #corners is a tuple: (top-right, bottom-right, top-left, bottom-left)
    kx = (self.width - hW) / 2 - 1
    ky = (self.length - hW) / 2 - 1
    self.room = []
    for y in range(self.length): #construct the room row by row
      row = []
      for x in range(self.width):
        if x > kx:
          if y > ky:
            i = TOP_RIGHT
          else:
            i = BOTTOM_RIGHT
        else:
          if y > ky:
            i = TOP_LEFT
          else:
            i = BOTTOM_LEFT
        if not corners[i]:
          tx = (x > 0) + (x == self.width - 1) #use template to find out which terrain to use
          ty = (y > 0) + (y == self.length - 1)
          char = smallTemplate[ty][tx]
        else:
          tx = (x > 0) + (x >= kx) + (x > kx) + (x > kx + hW) + (x > kx + hW + 1) + (x == self.width - 1)
          ty = (y > 0) + (y >= ky) + (y > ky) + (y > ky + hW) + (y > ky + hW + 1) + (y == self.length - 1)
          char = cornersTemplate[ty][tx]
        row.append(Tile(char, 0, [], True))
      self.room.append(row)
  def fillIn(self, char):
    for x, y in doublerange(self.width, self.length):
      self.getTile(x, y).ID = char
  def getWL(self): return self.width, self.length #return the dimensions
  def getTile(self, x, y): return self.room[y][x] #get a Tile object at specified coordinates
  def addDoors(self, doors):
    self.doors = addCards(self.doors, doors) #combine the current doors and the new doors info
    for x, y in doublerange(self.width, self.length): #add the doors to the actual room
      index = -1
      if   abs(y - (self.length - 1) / 2.0) < 1 and x == 0: index = WEST
      elif abs(y - (self.length - 1) / 2.0) < 1 and x == self.width - 1: index = EAST
      elif abs(x - (self.width - 1) / 2.0) < 1 and y == 0: index = NORTH
      elif abs(x - (self.width - 1) / 2.0) < 1 and y == self.length - 1: index = SOUTH
      if index >= 0 and doors[index]:
        tile = self.getTile(x, y)
        if doors[index] == CLOSED_DOOR:
          tile.ID = CLOSED_DOOR_ID
        elif doors[index] == LOCKED_DOOR:
          tile.ID = LOCKED_DOOR_ID
        else:
          tile.ID = DOOR_ID
        tile.color = DOOR_COLOR
  def addItems(self, density): #fill some tiles of a room randomly using density
    for x, y in doublerange(self.width, self.length):
      tile = self.getTile(x, y)
      if tile.ID == 1 and random.random() < density:
        tile.addItem(randItem())
  def randFill(self, density, char): #fill some tiles of a room randomly using density
    for x, y in doublerange(self.width, self.length):
      tile = self.getTile(x, y)
      if tile.ID == 1 and random.random() < density: tile.ID = char
  def getDoors(self): return self.doors
  def getVisibleWalls(self): #which walls have been fully seen
    #TODO implement visibleWalls
    return newCards(True)
  def hide(self):
    for y in range(self.length):
      for x in range(self.width):
        self.getTile(x, y).shown = False


def newMiniroom(shown, middle, color, doors, visible):
  return {'shown': shown, 'middle': middle, 'color': color, 'doors': doors, 'visible': visible, 'find': 0}


class Minimap: #2-D list of miniRooms
  def __init__(self, level):
    self.minimap = []
    for y in range(level.length):
      row = []
      for x in range(level.width):
        shown = False
        room = level.getRoom(x, y)
        roomWidth, roomLength = room.getWL()
        for x2, y2 in doublerange(roomWidth, roomLength):
          if room.getTile(x2, y2).shown: shown = True
        middle = color = 0
        for x2, y2 in doublerange(roomWidth, roomLength):
          terrain = room.getTile(x2, y2).ID
          if terrain == UP_STAIRS_ID or terrain == DOWN_STAIRS_ID:
            middle = terrain
            color = STAIRS_COLOR
        doors = room.getDoors()
        visible = room.getVisibleWalls()
        row.append(newMiniroom(shown, middle, color, doors, visible))
      self.minimap.append(row)
  def getMiniroom(self, x, y): return self.minimap[y][x]


#TODO level editor
#TODO getUpStairsXY() getDownStairsXY() or getStairPos hash table
class Level:
  'Contains a 2-D list of rooms'
  def __init__(self, type, name, *args):
    self.level = []
    self.upX = self.upY = self.downX = self.downY = 0
    self.name = name
    if type == RANDOM_LEVEL:
      self.width = random.randint(4, 6)
      self.length = random.randint(3, 5)
      roomWidth = randSkip(7, 17)
      roomLength = randSkip(7, 15)
      self.createStandard(roomWidth, roomLength)
    elif type == CUSTOM_LEVEL:
      self.width = args[0]
      self.length = args[1]
      self.createStandard(args[2], args[3])
  def createStandard(self, roomWidth, roomLength):
    self.newRooms(roomWidth, roomLength)
    self.addStairs()
    self.connectStairs()
    self.fillDeadRooms()
    self.hide()
  def getName(self):		return self.name
  def setName(self, name):	self.name = name
  def getWL(self):		return self.width, self.length #return the dimensions
  def getRoom(self, x, y):	return self.level[y][x]
  def newRooms(self, roomWidth, roomLength):
    for y in range(self.length): # make a 2-D list of rooms
      row = []
      for x in range(self.width):
        room = Room(roomWidth, roomLength, randCornerCards(0.35), 1, defaultSmallTemplate, hollowCornersTemplate)
        row.append(room)
      self.level.append(row)
  def checkForConnection(self, minimap, x, y, fill, lookFor): #used to see if the stairs are connected
  #TODO replace checkForConnection() and fill() with non-recursive functions
    miniroom = minimap.getMiniroom(x, y)
    if miniroom['find'] == fill: return False
    if miniroom['find'] == lookFor: return True
    miniroom['find'] = fill
    doors = miniroom['doors']
    if doors[WEST] and self.checkForConnection(minimap, x - 1, y, fill, lookFor): return True
    if doors[EAST] and self.checkForConnection(minimap, x + 1, y, fill, lookFor): return True
    if doors[NORTH] and self.checkForConnection(minimap, x, y - 1, fill, lookFor): return True
    if doors[SOUTH] and self.checkForConnection(minimap, x, y + 1, fill, lookFor): return True
    return False
  def addStairs(self): #adds both up and down stairs to the level
    minStairDistance = (self.width ** 2 + self.length ** 2) / 6.0
#    log(4, '    min Stair Distance', minStairDistance)
    while (self.upX - self.downX) ** 2 + (self.upY - self.downY) ** 2 < minStairDistance:
      self.upX = random.randrange(self.width)
      self.upY = random.randrange(self.length)
      self.downX = random.randrange(self.width)
      self.downY = random.randrange(self.length)
#      log(4, '    Stair Distance', (self.upX-self.downX)**2 + (self.upY-self.downY)**2)
    upRoom = self.getRoom(self.upX, self.upY)
    downRoom = self.getRoom(self.downX, self.downY)
    upWidth, upLength = upRoom.getWL()
    downWidth, downLength = downRoom.getWL()
    upRoom.getTile(int(upWidth / 2), int(upLength / 2)).ID = UP_STAIRS_ID
    downRoom.getTile(int(downWidth / 2), int(downLength / 2)).ID = DOWN_STAIRS_ID
  def connectStairs(self):
    connected = False
    while not connected:
      doors = [NO_DOOR, NO_DOOR, NO_DOOR, NO_DOOR]
      i = random.randrange(4)
      x = random.randrange(self.width)
      y = random.randrange(self.length)
      x2 = x
      y2 = y
      doors[i] = randDoorState()
      doors = tuple(doors)
      #TODO convert direction/i to dx, dy
      if   i == 0: y2 -= 1 #north
      elif i == 1: x2 += 1 #east
      elif i == 2: y2 += 1 #south
      elif i == 3: x2 -= 1 #west
      doors2 = flipCard(doors)
      if x2 >= 0 and x2 < self.width and y2 >= 0 and y2 < self.length:
        self.getRoom(x, y).addDoors(doors)
        self.getRoom(x2, y2).addDoors(doors2)
        minimap = Minimap(self)
#        for x, y in doublerange(self.width, self.length): #TODO make connecting staris more efficient
#          minimap.getMiniroom(x, y)['find'] = 0
        minimap.getMiniroom(self.downX, self.downY)['find'] = 2
        connected = self.checkForConnection(minimap, self.upX, self.upY, 1, 2)
  def fillDeadRooms(self):
    minimap = Minimap(self)
#    for x, y in doublerange(self.width, self.length):
#      minimap.getMiniroom(x, y)['find'] = 0
    self.fill(minimap, self.upX, self.upY, 1)
    #TODO remove rows and columns of dead rooms or add hallways into them
    for x, y in doublerange(self.width, self.length):
      if minimap.getMiniroom(x, y)['find'] == 0:
        self.getRoom(x, y).fillIn(BLOCK_ID)
  def fill(self, minimap, x, y, fill): #used to see if the stairs are connected
    miniroom = minimap.getMiniroom(x, y)
    if miniroom['find'] == fill: return
    miniroom['find'] = fill
    doors = miniroom['doors']
    if doors[WEST]: self.fill(minimap, x - 1, y, fill)
    if doors[EAST]: self.fill(minimap, x + 1, y, fill)
    if doors[NORTH]: self.fill(minimap, x, y - 1, fill)
    if doors[SOUTH]: self.fill(minimap, x, y + 1, fill)
  def findChar(self, char):
    for x, y in doublerange(self.width, self.length):
      room = self.getRoom(x, y)
      roomWidth, roomLength = room.getWL()
      for x2, y2 in doublerange(roomWidth, roomLength):
        if room.getTile(x2, y2).ID == char: return x, y, x2, y2
    return 0, 0, 0, 0
  def hide(self):
    for x, y in doublerange(self.width, self.length):
      self.getRoom(x, y).hide()
  def loadRoom(self, levelX, levelY):
    room = self.getRoom(levelX, levelY)
    roomWidth, roomLength = room.getWL()
    return room, roomWidth, roomLength


class Levelset: #TODO add dungeon branches
  def __init__(self, levels):
    self.levels = levels
    self.height = len(levels)
    log(8, '  ===== new Levelset height: ' + str(self.height) + ' =====')
  def getHeight(self): return self.height
  def getLevel(self, i): return self.levels[i]
  def getStartingPos(self):
    level = self.getLevel(0)
    levelX, levelY, roomX, roomY = level.findChar(UP_STAIRS_ID)
    pos = newPos(0, levelX, levelY, roomX, roomY)
    return pos


def randomLevelset(height):
  log(6, '  ===== creating ' + str(height) + ' random levels =====')
  levels = []
  for i in range(height):
    levels.append(Level(RANDOM_LEVEL, 'Dlvl:' + str(i)))
  return Levelset(levels)


#TODO add a stats dictionary for all the ailments/bonuses
#TODO add entities class (or use creatures for it)
class Creature:
  def __init__(self, levelset, position, maxHealth):
    self.levelset = levelset
    self.pos = position
    self.health = maxHealth
    self.maxHealth = maxHealth
    self.healthTimer = 0
    self.name = 'creature'
    self.inverted = False
  def isInverted(self):			return self.inverted
  def setInverted(self, inverted):	self.inverted = inverted
  def getChar(self):		return MONSTER_ID
  def getName(self):		return self.name
  def getColor(self):		return MONSTER_COLOR
  def getHealth(self):		return self.health
  def getMaxHealth(self):	return self.maxHealth
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
  def displayHP(self, screen, y, x):
    i = int(self.health * (len(healthColors) - 1.0) / self.maxHealth)
    screen.addstr(y, x, 'HP:')
    screen.addstr(y, x + 3, str(self.health) + '/' + str(self.maxHealth), curses.color_pair(healthColors[i]))
  def healthAct(self):
    self.healthTimer -= 1
    if self.healthTimer < 1:
      self.healthTimer = 10
      self.changeHealth(1)
    return True
  def getLevelset(self):	return self.levelset
  def getPos(self):		return self.pos
  def setName(self, name):	self.name = name
  def getName(self):		return self.name
  def loadLevel(self, stairsChar):
    level = self.levelset.getLevel(self.pos['z'])
    levelX, levelY, roomX, roomY = level.findChar(stairsChar)
    self.pos['levelX'] = levelX
    self.pos['levelY'] = levelY
    self.pos['roomX'] = roomX
    self.pos['roomY'] = roomY
  def goUp(self):
    if self.pos['z'] <= 0: return False
    self.pos['z'] -= 1
    log(4, self.getName() + ' went up a dungeon level. z', self.pos['z'])
    self.loadLevel(DOWN_STAIRS_ID)
    return True
#TODO do not use stairs if there is a creature in the way
  def goDown(self):
    if self.pos['z'] >= self.levelset.getHeight() - 1: return False
    self.pos['z'] += 1
    log(4, self.getName() + ' went down a dungeon level. z', self.pos['z'])
    self.loadLevel(UP_STAIRS_ID)
    return True
  def getLevel(self):
    return self.levelset.getLevel(self.pos['z'])
  def getRoom(self):
    return self.getLevel().getRoom(self.pos['levelX'], self.pos['levelY'])
  def wander(self, creatures):
    return self.move(random.randint(-1, 1), random.randint(-1, 1), creatures)
  def move(self, dx, dy, creatures):
    #TODO attack in next room
    if dx == 0 and dy == 0: return False
    level = self.getLevel()
    levelWidth, levelLength = level.getWL()
    room = level.getRoom(self.pos['levelX'], self.pos['levelY'])
    roomWidth, roomLength = room.getWL()
    x2 = self.pos['roomX'] + dx
    y2 = self.pos['roomY'] + dy
    if x2 < -1 or x2 > roomWidth or y2 < -1 or y2 > roomLength:
      return False, None
    terrain = room.getTile(self.pos['roomX'], self.pos['roomY']).ID
    newTerrain = room.getTile(limit(x2, 0, roomWidth - 1), limit(y2, 0, roomLength - 1)).ID
    if newTerrain in solid: #comment these two lines
      return False #to walk through walls
    enemy = creatures.findAt(self.pos['z'], self.pos['levelX'], self.pos['levelY'], x2, y2)
    if enemy is not None:
      #if self.attack(enemy): return True
      enemy.takeDamage(1) #TODO different amounts of damage, only attack enemies
      return True #return it
    #if moving diagonally and standing on a door or attempting to move on to one
    if dx != 0 and dy != 0 and DOOR_ID in [terrain, newTerrain]:
      return False
    self.pos['roomX'] = x2
    self.pos['roomY'] = y2
    if self.pos['roomX'] < 0 and self.pos['levelX'] > 0:
      self.pos['levelX'] -= 1
      oldRoomLength = roomLength
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      self.pos['roomX'] = roomWidth - 1
      if not roomLength == oldRoomLength: self.pos['roomY'] = int(roomLength / 2)
    elif self.pos['roomX'] > roomWidth - 1 and self.pos['levelX'] < levelWidth - 1:
      self.pos['levelX'] += 1
      oldRoomLength = roomLength
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      self.pos['roomX'] = 0
      if not roomLength == oldRoomLength: self.pos['roomY'] = int(roomLength / 2)
    elif self.pos['roomY'] < 0 and self.pos['levelY'] > 0:
      self.pos['levelY'] -= 1
      oldRoomWidth = roomWidth
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      if not roomWidth == oldRoomWidth: self.pos['roomX'] = int(roomWidth / 2)
      self.pos['roomY'] = roomLength - 1
    elif self.pos['roomY'] > roomLength - 1 and self.pos['levelY'] < levelLength - 1:
      self.pos['levelY'] += 1
      oldRoomWidth = roomWidth
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      if not roomWidth == oldRoomWidth: self.pos['roomX'] = int(roomWidth / 2)
      self.pos['roomY'] = 0
    self.pos['roomX'] = limit(self.pos['roomX'], 0, roomWidth - 1)
    self.pos['roomY'] = limit(self.pos['roomY'], 0, roomLength - 1)
    return True


class Monster(Creature):
  def init(self, type, level):
    self.type = type
    cfg = monsters[type]
    self.name = cfg.name
    self.char = cfg.ID
    self.color = cfg.color
    self.health = self.maxHealth = cfg.HP
    self.exp = level + cfg.exp
  def getChar(self): return self.char
  def getName(self): return self.name
  def getColor(self): return self.color
  def act(self, creatures):
    #TODO remember where the player was last seen and navigate there even if it is in a different room
    player = creatures.getPlayer()
    x1 = self.pos['levelX']
    y1 = self.pos['levelY']
    playerPos = player.getPos()
    x2 = playerPos['levelX']
    y2 = playerPos['levelY']
    terrain = self.getRoom().getTile(self.pos['roomX'], self.pos['roomY']).ID
    if x1 != x2 or y1 != y2:
      if terrain == UP_STAIRS_ID and randBool():
        self.goUp()
      elif terrain == DOWN_STAIRS_ID and randBool():
        self.goDown()
      else:
        for i in range(10):
          if self.wander(creatures): return True
      return True
    x1 = self.pos['roomX']
    y1 = self.pos['roomY']
    x2 = playerPos['roomX']
    y2 = playerPos['roomY']
    dx = dy = 0
    if x2 > x1: dx = 1
    if x2 < x1: dx = -1
    if y2 > y1: dy = 1
    if y2 < y1: dy = -1
    room = self.getRoom()
    if dx != 0 and dy != 0:
      newterrain = room.getTile(self.pos['roomX'] + dx, self.pos['roomY'] + dy).ID
      if terrain == DOOR_ID or newterrain in solid:
        newterrainX = room.getTile(self.pos['roomX'] + dx, self.pos['roomY']).ID
        newterrainY = room.getTile(self.pos['roomX'], self.pos['roomY'] + dy).ID
        if newterrainX in solid: dx = 0
        elif newterrainY in solid: dy = 0
    self.move(dx, dy, creatures)
    return True


class Player(Creature):
  def getChar(self): return PLAYER_ID
  def getColor(self): return PLAYER_COLOR
  def getMask(self):
    try:
      return self.mask
    except:
      self.mask = [[False for i in range(roomWidth)] for i in range(roomLength)]
      return self.mask
  def raycast(self):
  #TODO @memoize raycast directions
  #TODO creatures can raycast and store a mask of their own
    startX = self.pos['roomX']
    startY = self.pos['roomY']
    room = self.getRoom()
    roomWidth, roomLength = room.getWL()
    self.mask = [[False for i in range(roomWidth)] for i in range(roomLength)]
    self.mask[startY][startX] = True
    room.getTile(startX, startY).shown = True
#    for i in range(100):
    direction = 0
    while direction <= 2 * math.pi:
#      direction = i * 2 * math.pi / 100
      x = startX
      y = startY
      walls = 0
      distance = 0
      while walls < 1 and distance < 15:
        distance += 1
        x += math.cos(direction)
        y += math.sin(direction)
        xint = int(x + .5)
        yint = int(y + .5)
        #x2 = (int(x), int(math.ceil(x)))
        #y2 = (int(y), int(math.ceil(y)))
        #for xint, yint in itertools.product(x2, y2):
        if True:
        #for xint, yint in zip(x2, y2):
          if xint > roomWidth - 1 or yint > roomLength - 1 or xint < 0 or yint < 0:
            pass #walls += 1
          else:
            #x2, y2, = xint, yint
            #for xint, yint in itertools.product((x2 - 1, x2, x2 + 1), (x2 - 1, x2, x2 + 1)):
            self.mask[yint][xint] = True
            tile = room.getTile(xint, yint)
            tile.shown = True
            char = tile.ID
            if char in opaque: walls += 1
      #tmp = .7 * math.pi / distance**2
      #direction += tmp
      #log(1, tmp)
      direction += .001 * math.pi
      #direction += .002 * math.pi
  def act(self, creatures, key, moveOpts): #returns whether or not the player moved/took an action
    level = self.getLevel()
    levelWidth, levelLength = level.getWL()
    room = self.getRoom()
    roomWidth, roomLength = room.getWL()
    dx = (-1, 0, 1, 1, 1, 0, -1, -1)
    dy = (1, 1, 1, 0, -1, -1, -1, 0)
    for i in range(8): #TODO arrows/wasd double press controls
      if key == moveOpts[i][2]:
        return self.move(dx[i], dy[i], creatures)
    terrain = room.getTile(self.pos['roomX'], self.pos['roomY']).ID
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
        room = level.getRoom(levelX, levelY)
        for roomX, roomY in doublerange(room.getWL()):
          tile = room.getTile(roomX, roomY)
          if not tile.ID in solid and frequency > random.random():
            pos = newPos(z, levelX, levelY, roomX, roomY)
            monster = randMonster(levelset, pos, z)
            self.creatures.append(monster)
    log(4, 'Added ' + str(len(self.creatures) - 1) + ' monsters.') #-1 for the player
  def getList(self): return self.creatures
  def getPlayer(self): return self.creatures[0]
  def getStatsString(self):
    stats = 'Creatures: '
    for c in self.creatures:
      stats += '[' + chars[c.getChar()] + ', ' + c.getName() + ', HP:' + str(c.getHealth()) + '/' + str(c.getMaxHealth()) + ']'
    return stats
  def removeDead(self): # Bring out your dead!
    #rebuild the list, excluding creatures that return false for isAlive()
    self.creatures = [creature for creature in self.creatures if creature.isAlive()]
  def act(self):
    self.removeDead()
    playerZ = self.getPlayer().getPos()['z']
    for creature in self.creatures[1:]: #loop over a copy of creatures that excludes the 1st item (the player)
      #the copy also keeps it from messing up if one dies
      if creature.getPos()['z'] != playerZ: continue #only creatures on the same level as the player get to act
      creature.healthAct() #let each creature autoheal
      creature.act(self) #tell each creature to do its thing
      self.removeDead() #if it or any other creature died while on its turn, remove it
    return True
  def findAt(self, z, levelX, levelY, roomX, roomY):
    for creature in self.creatures:
      pos = creature.getPos()
      if pos['z'] != z: continue
      if pos['levelX'] != levelX: continue
      if pos['levelY'] != levelY: continue
      if pos['roomX'] != roomX: continue
      if pos['roomY'] != roomY: continue
      return creature
    return None


def display(screen, creatures):
  player = creatures.getPlayer()
  mask = player.getMask()
  plpos = player.getPos()

  level = player.getLevel()
  room = level.getRoom(plpos['levelX'], plpos['levelY'])
  roomWidth, roomLength = room.getWL()
  levelWidth, levelLength = level.getWL()

  screen.clear()
  #  creatureStats = creatures.getStatsString()
  line1 = player.getName() + '  ' + level.getName()
  screen.addstr(1, 0, line1)
  player.displayHP(screen, 1, len(line1) + 2)

  roomDispX = levelWidth * 5 + 3
  roomDispY = 5
  #                       h,l,y,x
  miniWin = curses.newwin(levelLength * 3 + 2, levelWidth * 5 + 2, roomDispY, 0)
  miniWin.border()

  minimap = Minimap(level)

  for x, y in doublerange(levelWidth, levelLength):
    miniroom = minimap.getMiniroom(x, y)
    if miniroom['shown']:
      middle = miniroom['middle']
      color = miniroom['color']
      if x == plpos['levelX'] and y == plpos['levelY']:
        middle = player.getChar()
        color = PLAYER_COLOR
      miniWin.addstr(2 + y * 3, 2 + x * 5, '[ ]')
      miniWin.addch(2 + y * 3, 3 + x * 5, chars[middle], curses.color_pair(color))
      doors = miniroom['doors']
      visible = miniroom['visible']
      char = ''
      if not visible[NORTH]: char = '?'
      elif doors[NORTH]: char = '|'
      else: char = ' '
      miniWin.addch(1 + y * 3, 3 + x * 5, char)

      if not visible[SOUTH]: char = '?'
      elif doors[SOUTH]: char = '|'
      else: char = ' '
      miniWin.addch(3 + y * 3, 3 + x * 5, char)

      if not visible[WEST]: char = '?'
      elif doors[WEST]: char = '-'
      else: char = ' '
      miniWin.addch(2 + y * 3, 1 + x * 5, char)

      if not visible[EAST]: char = '?'
      elif doors[EAST]: char = '-'
      else: char = ' '
      miniWin.addch(2 + y * 3, 5 + x * 5, char)

  #TODO BUG fix the room window needing 1 extra length/width (roomWidth + 1)
  roomWin = curses.newwin(roomLength, roomWidth + 1, roomDispY, roomDispX)
#  roomWin.border()

  for x, y in doublerange(roomWidth, roomLength):
    tile = room.getTile(x, y)
    char = tile.getTopID() #Terrain()
    color = tile.getTopColor()
    bold = 0
    if mask[y][x]: bold = curses.A_BOLD
    if not tile.shown: char = color = 0

    roomWin.addch(y, x, chars[char], curses.color_pair(color) + bold)
  for creature in reversed(creatures.getList()):
    pos = creature.getPos()
    if pos['z'] != plpos['z']: continue
    if pos['levelX'] != plpos['levelX']: continue
    if pos['levelY'] != plpos['levelY']: continue
    if not mask[pos['roomY']][pos['roomX']]: continue
    char = creature.getChar()
    color = creature.getColor()
    roomWin.addch(pos['roomY'], pos['roomX'], chars[char],
                  curses.color_pair(color) + curses.A_REVERSE * creature.isInverted())

  screen.noutrefresh() #mark each screen for refresh but wait
  roomWin.noutrefresh()
  miniWin.noutrefresh()
  curses.doupdate() #refresh all screens at the same time
  screen.move(roomDispY + plpos['roomY'], roomDispX + plpos['roomX']) #move the cursor to the player


#TODO improve options
#TODO default options file
#TODO arrow keys double press controls (or wasd double press)
def optionsMenu(moveOpts):
  quit = False
  #                   h,  l,  y, x
  win = curses.newwin(19, 27, 0, 0)
  win.clear()
  win.border()
  while not quit:
    win.addstr(1, 7, 'Options')
    for i in range(1, len(moveOpts)):
      y = i + 3
      option = moveOpts[i]
      win.addstr(y, 2, option[0])
      reverse = option[3] * curses.A_REVERSE
      if i > 8:
        win.addstr(y, 14, option[1], reverse)
      else:
        win.addch(y, 14, option[1], reverse)
    win.addstr(y + 2, 4, 'Press q to quit')
    key = win.getkey()
    win.refresh()

    if key == '1':
      moveOpts[9][3] = True
      moveOpts[10][3] = False
      moveOpts[11][3] = False
      for i in range(8):
        moveOpts[i][1] = ('1', '2', '3', '6', '9', '8', '7', '4')[i]
        moveOpts[i][2] = moveOpts[i][2] #('1', '2', '3', '6', '9', '8', '7', '4')[i]
    elif key == '2':
      moveOpts[9][3] = False
      moveOpts[10][3] = True
      moveOpts[11][3] = False
      for i in range(8):
        moveOpts[i][1] = ('1', 'v', '3', '>', '9', '^', '7', '<')[i]
        moveOpts[i][2] = ('1', 'KEY_DOWN', '3', 'KEY_RIGHT', '9', 'KEY_UP', '7', 'KEY_LEFT')[i]
    elif key == '3':
      moveOpts[9][3] = False
      moveOpts[10][3] = False
      moveOpts[11][3] = True
      for i in range(8):
        moveOpts[i][1] = ('Z', 'X', 'C', 'D', 'E', 'W', 'Q', 'A')[i]
        moveOpts[i][2] = moveOpts[i][1].lower() #('z', 'x', 'c', 'd', 'e', 'w', 'q', 'a')[i]
    #q, enter key, or spacebar
    elif key in ('q', '\n', ' '):
      quit = True
  return moveOpts


defaultLegalChars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_ ')


def textField(screen, yPos, xPos, prompt, sizeLimit, legalChars=defaultLegalChars):
  height, width = screen.getmaxyx()
  screen.addstr(yPos, xPos, prompt)
  xPos += len(prompt)
  x = 0
  text = ''
  while True:
    length = len(text)
    x = limit(x, 0, length)
    screen.addstr(yPos, xPos, text + ' ')
    screen.move(yPos + (xPos + x) / width, (xPos + x) % width)
    key = screen.getkey()
#    log(1, 'key pressed', key)
#    if len(key) == 1: log(1, 'key code', ord(key))
    if   key == 'KEY_LEFT': x -= 1
    elif key == 'KEY_RIGHT': x += 1
    elif key == 'KEY_HOME': x = 0
    elif key == 'KEY_END': x = length
    elif key == '\n': return text
    elif len(key) == 1 and ord(key) == 27: break #ESC key
    elif key == 'KEY_BACKSPACE':
      if length == 0:
        break
      if x > 0:
        x -= 1
        text = text[:x] + text[x + 1:]
    elif key == 'KEY_DC': #delete key
      if x < length:
        text = text[:x] + text[x + 1:]
    elif length < sizeLimit:
      if key in legalChars:
        text = text[:x] + key + text[x:]
        x += 1
#      else: log(1, 'illegal character')
  return ''


#movement key options
defaultMoveOpts = [
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

def logo(screen):
#  screen.addstr(0, 3, r'  _____                                      ')
#  screen.addstr(1, 3, r' / ___ \                        ___          ')
#  screen.addstr(2, 3, r'/ /   \ \                       | |          ')
#  screen.addstr(3, 3, r'| |   | | ___ ___  ____   ____ (   )         ')
#  screen.addstr(4, 3, r'| |  _J | | | | | / __ \ / __/  | |          ')
#  screen.addstr(5, 3, r'\ \__\ \/ | \_J | | ___V \__ \  | |__        ')
#  screen.addstr(6, 3, r' \____\ \ \____/| \___|  /___A  \___N        ')
#  screen.addstr(7, 3, r'       \_\                                   ')

  screen.addstr(0, 3, r'========================================')
  screen.addstr(1, 3, r')     ________                         (')
  screen.addstr(1, 3, r')    /_______/\                        (')
  screen.addstr(2, 3, r')   /  ____  \/                ___     (')
  screen.addstr(3, 3, r')   ) /(   \ ()_ ___ ___  _____) (__   (')
  screen.addstr(4, 3, r')   ) (\__ ) ) ( ) (/ _ \/ ____   _/   (')
  screen.addstr(5, 3, r')   ) \_\ \/ ) (_) ( /__/\__ \ ) (_    (')
  screen.addstr(6, 3, r')   \____\ \/ \___/|\________/ \___|   (')
  screen.addstr(7, 3, r'==========\_)===========================')



def yesNoPrompt(screen, y, x, prompt, default=None):
  defaultStr = {True: '[y]', False: '[n]', None: ''}[default]
  prompt = str(prompt) + ' (y/n)' + defaultStr
  screen.addstr(y, x, prompt)
  screen.refresh()
  key = ''
  input = None
  while input is None:
    key = screen.getkey()
    log(1, 'key pressed', key)
    if key.lower() == 'y': input = True
    if key.lower() == 'n': input = False
    if input is None: input = default #if the user pressed something else, use the default if there is one
  screen.addstr(y, x, ' ' * len(prompt)) #clear the prompt message
  screen.refresh()
  return input


def deathMessage(screen):
  #                   h, l,  y, x
  win = curses.newwin(4, 17, 0, 6)
  win.border()
  win.addstr(1, 4, 'You Died!') #TODO improve player death message
  win.addstr(2, 1, 'Press q to quit')
  win.refresh()
  key = ' '
  while key != 'q':
    key = screen.getkey()

MSG_POS = (0, 0) #x, y
MENU_MSG_POS = (0, 11) #x, y

def saveGame(saveFilePath, screen, creatures, moveOpts):
  startTime = time.time()
  screen.addstr(MSG_POS[1], MSG_POS[0], 'Saving game...')
  screen.refresh()
  s = signal.signal(signal.SIGINT, signal.SIG_IGN) #ignore keyboard interrupts
  metadata = (VERSION, moveOpts)
  #jsonWrite((metadata, creatures), saveFilePath) #save the game
  file = gzip.open(saveFilePath, 'wb')
  pickle.dump((metadata, creatures), file) #save the game
  file.close()
  signal.signal(signal.SIGINT, s) #enable keyboard interrupts again
  log(10, 'Game saved at', saveFilePath)
  log(20, 'Game save time', time.time() - startTime)


class VersionError(Exception): pass

def loadGame(saveFilePath, screen):
  startTime = time.time()
  screen.addstr(MENU_MSG_POS[1], MENU_MSG_POS[0], 'Loading save file...')
  screen.refresh()
  file = gzip.open(saveFilePath, 'rb')
  try:
#    creatures, metadata = jsonRead(saveFilePath)
    (metadata, creatures) = pickle.load(file)
    #log(1, metadata)
    if metadata[0] != VERSION:
      raise VersionError('Save file from old version (' + metadata[0] +
                         ') not compatible with current version (' + VERSION + ').')
  except EOFError:
    if yesNoPrompt(screen, MENU_MSG_POS[1], MENU_MSG_POS[0], 'The save file is corrupt. Delete it?'):
      os.remove(saveFilePath)
      log(10, 'File deleted', saveFilePath)
    else:
      newPath = os.path.join(ROOT_DIR, os.path.basename(saveFilePath))
      os.rename(saveFilePath, newPath)
      log(10, saveFilePath + ' moved to', newPath)
    raise
  finally:
    file.close()
  player = creatures.getPlayer()
  levelset = player.getLevelset()
  log(10, 'Game loaded from', saveFilePath)
  os.remove(saveFilePath)
  log(20, 'Game load time', time.time() - startTime)
  return levelset, player, creatures, metadata


#TODO add levels when they are reached instead of all at startup
def newGame(screen, height, creatureFrequency, playerName):
  startTime = time.time()
  screen.addstr(MENU_MSG_POS[1], MENU_MSG_POS[0], 'Please wait a moment while I dig the dungeon...')
  screen.refresh()
  #good layout: level:6x3 room:13x11 or 15x11
  levelset = randomLevelset(height)
  player = Player(levelset, levelset.getStartingPos(), 100)
  player.setName(playerName)
  player.setInverted(True)

  #generate the monsters
  creatures = Creatures(levelset, creatureFrequency, player)
  log(20, 'Game creation time', time.time() - startTime)
  return levelset, player, creatures


def main(screen):
  if not os.path.exists(SAVE_GAME_DIR):
    os.makedirs(SAVE_GAME_DIR)

  log(1000, '==== Quest Log File ====')
  log(10, 'Found cPickle?', cPickleFound)

  screen.clear() #Clear terminal screen
  curses.curs_set(2) #set cursor to block mode
  charsInit()

  saveFiles = os.listdir(SAVE_GAME_DIR)

  log(3, 'Games will be saved in', SAVE_GAME_DIR)
  log(3, 'Save Files', saveFiles)

  playerName = ''
  levelset = player = creatures = None

  if len(sys.argv) == 2:
    playerName = sys.argv[1]
  screen.clear()
  logo(screen)
  while len(playerName) == 0:
    playerName = textField(screen, 9, 0, 'What is your name? ', 60)
  log(5, 'Player Name', playerName)
  saveFilePath = os.path.join(SAVE_GAME_DIR, playerName + '.save')
  log(5, 'Save file path', saveFilePath)
  try:
    levelset, player, creatures, metadata = loadGame(saveFilePath, screen)
    moveOpts = metadata[1]
  except (IOError, EOFError) as e: #could not find/read the file
    levelset, player, creatures = newGame(screen, 20, 0.01, playerName)
    moveOpts = defaultMoveOpts
  except VersionError as e:
    screen.addstr(MENU_MSG_POS[1], MENU_MSG_POS[0], str(e), curses.color_pair(18))
    screen.addstr(' Press any key to exit.')
    screen.getkey()
    quit()
  try:
    while True:
      if not player.isAlive():
        deathMessage(screen)
        return
      player.raycast()
      display(screen, creatures)
      key = screen.getkey()
      player.healthAct()
      while not player.act(creatures, key, moveOpts):
        if key == 'S':
          if yesNoPrompt(screen, MSG_POS[1], MSG_POS[0], 'Really save and quit?', True):
            saveGame(saveFilePath, screen, creatures, moveOpts)
            return
          display(screen, creatures)
        if key == 'o':
          optionsMenu(moveOpts)
          display(screen, creatures)
        elif key == '#':
          command = textField(screen, MSG_POS[1], MSG_POS[0], '# ', 60) #TODO autocomplete commands
          log(10, 'Extended Command', command)
          if command == 'quit' and yesNoPrompt(screen, MSG_POS[1], MSG_POS[0], 'Really quit without saving?', False):
            return
          display(screen, creatures)
        key = screen.getkey()
      creatures.act()
  except KeyboardInterrupt:
    log(1, 'KeyboardInterrupt - saving game')
    saveGame(saveFilePath, screen, creatures, moveOpts)
    return

curses.wrapper(main)
print ('See you later...')
