#!/usr/bin/python
import os, random, math, time, curses, sys, itertools, gzip
try: import cPickle as pickle #cPickle is faster than pickle
except: import pickle #if cPickle does not exist, use pickle

#TODO think of a better name for the game
#TODO ssh server to play the game on
#TODO messages
#TODO "You hear a sound to the west." telling you a monster moved there
#TODO level editor
#TODO add comments

#these are the ID numbers for different items and terrain
UP_STAIRS_ID = 3
DOWN_STAIRS_ID = 4
DOOR_ID = 12
PLAYER_ID = 2
BLOCK_ID = 5
ALPHABET_OFFSET = 13

DOOR_COLOR = 20
STAIRS_COLOR = 15
PLAYER_COLOR = 14

#TODO use level types to generate different layouts
RANDOM_LEVEL = 0
CUSTOM_LEVEL = 1
LEVEL_FROM_FILE = 2 #TODO town level at the top

#TODO creature level and rarity
monsters = (
{'name':'bat',		'char':14, 'color':14, 'HP': 2}, #0
{'name':'snake',	'char':31, 'color':16, 'HP': 7}, #1
{'name':'dragon',	'char':42, 'color':18, 'HP':30}, #2
{'name':'spider',	'char':31, 'color':17, 'HP': 5}, #3
{'name':'zombie',	'char':64, 'color':16, 'HP': 3}, #4
{'name':'newt',		'char':26, 'color':20, 'HP': 1}, #5
{'name':'skeleton',	'char':57, 'color':19, 'HP':10}, #6
{'name':'owlbear',	'char':40, 'color':20, 'HP':14}  #7
)

healthColors = (9,10,11,12,13)

solid = (5,6,7,8,9,10,11) #cannot move through
opaque = (5,6,7,8,9,10,11,12) # cannot see through
chars = () #run initializeChars() to initialize these

def initializeChars():  #chars = '.#^!-*:++;[???---////()?[[[]]]]'
  global chars
  #these are the types of terrain and items

  chars = (	   ' ',	#  0 empty
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
  'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'
#		   ' ',	# 65
  )

  #color combinaions of foreground, background
  curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_RED)
  curses.init_pair(10, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)
  curses.init_pair(12, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(13, curses.COLOR_WHITE, curses.COLOR_GREEN)


  curses.init_pair(14, curses.COLOR_BLUE, curses.COLOR_BLACK)
  curses.init_pair(15, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(16, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(17, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.init_pair(18, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(19, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(20, curses.COLOR_YELLOW, curses.COLOR_BLACK)

rootDir = os.path.join(os.path.expanduser('~'), '.quest') #root dir at /home/user/.quest/
saveGameDir = os.path.join(rootDir,'save') #where the games will be saved
logfile = os.path.join(rootDir, 'log.txt') #where the log output will appear
logContents = []
repeated = 0
logMinPriority = 0 #used to prioritize logged info (low numbers are low priority)

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

#implementation of xrange that works in python 2 and 3
#it has the effect of speeding up the range function in python 2
def range(start, stop=None, step=1):
  if stop is None:
    stop = start
    start = 0
  while start < stop:
    yield start
    start += step

#restricts the imput to be between min and max
def limit(value, minval, maxval): return min(maxval, max(minval, value))

#random even/odd numbers (depending on whether min is even or odd)
def randSkip(start, stop): return random.choice(list(range(start, stop, 2)))

def doublerange(xlen, ylen=0):
  if ylen == 0 and xlen.__class__ in [tuple, list]:
    return doublerange(xlen[0], xlen[1])
  return itertools.product(range(xlen), range(ylen))

def newPos(z, levelX, levelY, roomX, roomY):
  return {'z':z, 'levelX':levelX, 'levelY':levelY, 'roomX':roomX, 'roomY':roomY}

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
  def __init__(self, terrainID, color, items, shown): #TODO (possibly) make terrain an item and add item colors
    self.terrainID = terrainID
    self.color = color
    self.items = items
    self.shown = shown
  #terrain is the material that is seen
  def setTerrain(self, ID):   self.terrainID = ID
  def getTerrain(self):       return self.terrainID

  def setColor(self, color):  self.color = color
  def getColor(self):         return self.color

  def setItems(self, items):  self.items = items
  def getItems(self):         return self.items
  def addItem(self, item):    self.items.append(item)
  def popItem(self):          return self.items.pop()

  def show(self):             self.shown = True
  def hide(self):             self.shown = False
  def isShown(self):          return self.shown #TODO Tile.isShown() might need to be on each creature

#Anything with 4 directions
def newCardinals(north, east, south, west):
  return {'north':north, 'east':east, 'south':south, 'west':west}

def newCardinalsFalse():
  return newCardinals(False, False, False, False)

def newCardinalsTrue():
  return newCardinals(True, True, True, True)

def directionName(i):
  if i==0: return 'north'
  if i==1: return 'east'
  if i==2: return 'south'
  if i==3: return 'west'

def directionIndex(name):
  if name=='north': return 0
  if name=='east': return 1
  if name=='south': return 2
  if name=='west': return 3

def invertCardinals(cards): #swap north with south and east with west
  return {'north':cards['south'], 'south':cards['north'], 'east':cards['west'], 'west':cards['east']}

def addCardinals(cards1, cards2):
  return newCardinals(
  cards1['north'] or cards2['north'],
  cards1['east'] or cards2['east'],
  cards1['south'] or cards2['south'],
  cards1['west'] or cards2['west'])

#TODO add room types
#TODO change room and level to a flattened list
class Room:
  'Contains one room of a level and all the objects in it.'
  def __init__(self, width, length): #create a new room
    self.doors = newCardinalsFalse()
    #minimum dimensions are 3x3
    if width<3: width = 3
    if length<3: length = 3
    #store the width and length
    self.width = width
    self.length = length
    #template defines the smallest room
    template = (
    ( 8, 6, 9),
    ( 7, 1, 7),
    (10, 6,11))
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
  def fillCorners(self, corners, hW): #hW = hallwayWidth
    #TODO fill only certain corners
    #corners is a dict with tl (top-left), tr (top-right), bl (bottom-left), and br (bottom-right)
    BL = BLOCK_ID
#    template = [
#    [BL, 7, 1, 7,BL],
#    [ 6,11, 1,10, 6],
#    [ 1, 1, 1, 1, 1],
#    [ 6, 9, 1, 8, 6],
#    [BL, 7, 1, 7,BL]
#    ]
    template = (
    (BL,BL, 8, 1, 9,BL,BL),
    (BL,BL, 7, 1, 7,BL,BL),
    ( 8, 6,11, 1,10, 6, 9),
    ( 1, 1, 1, 1, 1, 1, 1),
    (10, 6, 9, 1, 8, 6,11),
    (BL,BL, 7, 1, 7,BL,BL),
    (BL,BL,10, 1,11,BL,BL))
    kx = (self.width -hW)/2-1
    ky = (self.length-hW)/2-1
    for x, y in doublerange(self.width, self.length): #itertools.product(range(2,4), range(2,3)):
      tx = (x>0)+(x>=kx)+(x>kx)+(x>kx+hW)+(x>kx+hW+1)+(x==self.width-1)
      ty = (y>0)+(y>=ky)+(y>ky)+(y>ky+hW)+(y>ky+hW+1)+(y==self.length-1)
      if not (tx==3 or ty==3):#abs(y-(self.length-1)/2.0)<1 and not abs(x-(self.width -1)/2.0)<1:
        self.getTile(x,y).setTerrain(template[ty][tx])
  def fillIn(self, char):
    for x, y in doublerange(self.width, self.length):
      self.getTile(x, y).setTerrain(char)
  def getWL(self): return self.width, self.length  #return the dimensions
  def getTile(self, x, y): return self.room[y][x] # get a Tile object at specified coordinates
  def addDoors(self, doors):
    self.doors = addCardinals(self.doors, doors) #combine the current doors and the new doors info
    for x, y in doublerange(self.width, self.length): #add the doors to the actual room
      if doors['west']  and abs(y-(self.length-1)/2.0)<1 and x==0 \
      or doors['east']  and abs(y-(self.length-1)/2.0)<1 and x==self.width-1\
      or doors['north'] and abs(x-(self.width -1)/2.0)<1 and y==0 \
      or doors['south'] and abs(x-(self.width -1)/2.0)<1 and y==self.length-1: #TODO improve door creation if statement
        tile = self.getTile(x, y)
        tile.setTerrain(DOOR_ID)
        tile.setColor(DOOR_COLOR)
  def populate(self, density, char): #fill some tiles of a room randomly using density
    for x, y in doublerange(self.width, self.length):
      tile = self.getTile(x, y)
      if tile.getTerrain() == 1 and random.random() < density: tile.setTerrain(char)
  def getDoors(self): return self.doors
  def getVisibleWalls(self): #which walls have been fully explored
    shown = newCardinalsTrue()
#Disabled since it does not work on weirdly-shaped rooms

    """for x in range(self.width): #top row
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
"""

    return shown
  def hide(self):
    for y in range(self.length):
      for x in range(self.width):
        self.getTile(x, y).hide()

class Miniroom:
  def __init__(self, shown, middle, color, doors, visible):
    self.shown = shown
    self.middle = middle
    self.color = color
    self.doors = doors #openings in the wall
    self.visible = visible #visible walls
  def isShown(self):		return self.shown

  def getMiddle(self):		return self.middle
  def setMiddle(self, middle):	self.middle = middle

  def getColor(self):		return self.color
  def setColor(self, color):	self.color = color

  def getDoors(self):		return self.doors
  def getVisibleWalls(self):	return self.visible

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
          if room.getTile(x2, y2).isShown(): shown = True
        middle = color = 0
        for x2, y2 in doublerange(roomWidth, roomLength):
          terrain = room.getTile(x2, y2).getTerrain()
          if terrain == UP_STAIRS_ID or terrain == DOWN_STAIRS_ID:
            middle = terrain
            color = STAIRS_COLOR
        doors = room.getDoors()
        visible = room.getVisibleWalls()
        row.append(Miniroom(shown, middle, color, doors, visible))
      self.minimap.append(row)
  def getMiniroom(self, x, y): return self.minimap[y][x]

#TODO level editor
#TODO getUpStairsXY() getDownStairsXY() or getStairPos hash table
class Level:
  'Contains a 2-D list of rooms'
  def __init__(self, type, name, arg0=0, arg1=0, arg2=0, arg3=0):
#  def __init__(self, type, name, width, length, roomWidth, roomLength):
#    log(7, '    ===== new Level  =====')
#    log(7, '    type', type)
    self.level = []
    self.upX = self.upY = self.downX = self.downY = 0
    self.name = name
    if type == RANDOM_LEVEL:
      self.width = random.randint(4,6)
      self.length = random.randint(3,5)
      roomWidth = randSkip(7,17)
      roomLength = randSkip(7,15)
      self.createStandard(roomWidth, roomLength)
    elif type == CUSTOM_LEVEL:
      self.width = arg0
      self.length = arg1
      self.createStandard(arg2, arg3)

  def createStandard(self, roomWidth, roomLength):
    self.newRooms(roomWidth, roomLength)
    self.addStairs()
    self.connectStairs()
#    self.randomizeRooms()
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
        room = Room(roomWidth, roomLength)
        row.append(room)
      self.level.append(row)
  def checkForConnection(self, minimap, x, y, fill, lookFor): #used to see if the stairs are connected
    miniroom = minimap.getMiniroom(x, y)
    if miniroom.getMiddle() == fill: return False
    if miniroom.getMiddle() == lookFor: return True
    miniroom.setMiddle(fill)
    doors = miniroom.getDoors()
    if doors['west']:
      if self.checkForConnection(minimap, x-1, y, fill, lookFor): return True
    if doors['east']:
      if self.checkForConnection(minimap, x+1, y, fill, lookFor): return True
    if doors['north']:
      if self.checkForConnection(minimap, x, y-1, fill, lookFor): return True
    if doors['south']:
      if self.checkForConnection(minimap, x, y+1, fill, lookFor): return True
    return False
  def addStairs(self): #adds both up and down stairs to the level
    minStairDistance = (self.width**2+self.length**2)/6.0
#    log(4, "    min Stair Distance", minStairDistance)
    while (self.upX-self.downX)**2+(self.upY-self.downY)**2 < minStairDistance:
      self.upX = random.randrange(self.width)
      self.upY = random.randrange(self.length)
      self.downX = random.randrange(self.width)
      self.downY = random.randrange(self.length)
#      log(4, "    Stair Distance", (self.upX-self.downX)**2+(self.upY-self.downY)**2)

    upRoom = self.getRoom(self.upX, self.upY)
    downRoom = self.getRoom(self.downX, self.downY)
    upWidth, upLength = upRoom.getWL()
    downWidth, downLength = downRoom.getWL()
    upRoom.getTile(int(upWidth/2), int(upLength/2)).setTerrain(UP_STAIRS_ID)
    downRoom.getTile(int(downWidth/2), int(downLength/2)).setTerrain(DOWN_STAIRS_ID)
  def connectStairs(self):
    connected = False
    while not connected:
      doors = newCardinalsFalse()
      i = random.randrange(4)
      x = random.randrange(self.width)
      y = random.randrange(self.length)
      x2=x
      y2=y
      doors[directionName(i)] = True
      if   i==0: y2-=1 #north
      elif i==1: x2+=1 #east
      elif i==2: y2+=1 #south
      elif i==3: x2-=1 #west
      doors2 = invertCardinals(doors)
      if x2>=0 and x2<self.width and y2>=0 and y2<self.length:
        self.getRoom(x, y).addDoors(doors)
        self.getRoom(x2, y2).addDoors(doors2)
        minimap = Minimap(self)
        for x, y in doublerange(self.width, self.length): #TODO make connecting staris more efficient
          minimap.getMiniroom(x, y).setMiddle(0)
        minimap.getMiniroom(self.downX, self.downY).setMiddle(2)
        connected = self.checkForConnection(minimap, self.upX, self.upY, 1, 2)
  def randomizeRooms(self): #TODO Level.randomizeRooms()
    for x, y in doublerange(self.getWL()):
      #False is a placeholder
      self.getRoom(x, y).fillCorners(False, 3)
  def fillDeadRooms(self):
    minimap = Minimap(self)
    for x, y in doublerange(self.width, self.length):
      minimap.getMiniroom(x, y).setMiddle(0)
    self.fill(minimap, self.upX, self.upY, 1)
    #TODO remove rows and columns of dead rooms or add hallways into them
    for x, y in doublerange(self.width, self.length):
      if minimap.getMiniroom(x, y).getMiddle() == 0:
        self.getRoom(x, y).fillIn(BLOCK_ID)
  def fill(self, minimap, x, y, fill): #used to see if the stairs are connected
    miniroom = minimap.getMiniroom(x, y)
    if miniroom.getMiddle() == fill: return
    miniroom.setMiddle(fill)
    doors = miniroom.getDoors()
    if doors['west']:  self.fill(minimap, x-1, y, fill)
    if doors['east']:  self.fill(minimap, x+1, y, fill)
    if doors['north']: self.fill(minimap, x, y-1, fill)
    if doors['south']: self.fill(minimap, x, y+1, fill)
  def findChar(self, char):
    for x, y in doublerange(self.width, self.length):
      room = self.getRoom(x, y)
      roomWidth, roomLength = room.getWL()
      for x2, y2 in doublerange(roomWidth, roomLength):
        if room.getTile(x2, y2).getTerrain()==char: return x, y, x2, y2
    return 0,0,0,0
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
    log(8, '  ===== new Levelset height: '+str(self.height)+' =====')    
  def getHeight(self):	return self.height
  def getLevel(self, i):return self.levels[i]
  def getStartingPos(self):
    level = self.getLevel(0)
    levelX, levelY, roomX, roomY = level.findChar(UP_STAIRS_ID)
    pos = newPos(0, levelX, levelY, roomX, roomY)
    return pos

def randomLevelset(height):
  log(6, '  ===== creating '+str(height)+' random levels =====')
  levels = []
  for i in range(height):
    levels.append(Level(RANDOM_LEVEL, 'Dlvl:'+str(i)))
  return Levelset(levels)

#TODO add a stats dictionary for all the ailments/bonuses
#TODO add closed doors as a terrain or entity/creature
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
  def getChar(self): return MONSTER_ID
  def getName(self): return self.name
  def getColor(self): return MONSTER_COLOR
  def isInverted(self): return self.inverted
  def setInverted(self, inverted): self.inverted = inverted
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
  def displayHP(self, screen, y, x):
    i = int(self.health * (len(healthColors)-1.0) / self.maxHealth)
    screen.addstr(y,x, 'HP:')
    screen.addstr(y,x+3, str(self.health)+'/'+str(self.maxHealth), curses.color_pair(healthColors[i]))
  def healthAct(self):
    self.healthTimer -= 1
    if self.healthTimer < 1:
      self.healthTimer = 10
      self.changeHealth(1)
    return True
  def getLevelset(self): return self.levelset
  def getPos(self): return self.pos
  def setName(self, name): self.name = name
  def getName(self):       return self.name
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
    log(4, self.getName()+' went up a dungeon level. z', self.pos['z'])
    self.loadLevel(DOWN_STAIRS_ID)
    return True
#TODO BUG monsters going downstairs immediately die
#TODO BUG going down a floor messes up?
  def goDown(self):
    if self.pos['z'] >= self.levelset.getHeight()-1: return False
    self.pos['z'] += 1
    log(4, self.getName()+' went down a dungeon level. z', self.pos['z'])
    self.loadLevel(UP_STAIRS_ID)
    return True
  def getLevel(self):  return self.levelset.getLevel(self.pos['z'])
  def getRoom(self):
    return self.getLevel().getRoom(self.pos['levelX'], self.pos['levelY'])
  def wander(self, creatures):
    return self.move(random.randint(-1,1),random.randint(-1,1), creatures)
  def move(self, dx, dy, creatures):
    if dx==0 and dy==0: return False
    level = self.getLevel()
    levelWidth, levelLength = level.getWL()
    room = level.getRoom(self.pos['levelX'], self.pos['levelY'])
    roomWidth, roomLength = room.getWL()
    x2=self.pos['roomX']+dx
    y2=self.pos['roomY']+dy
    if x2<-1 or x2>roomWidth or \
    y2<-1 or y2>roomLength:
      return False, None
    terrain = room.getTile(self.pos['roomX'], self.pos['roomY']).getTerrain()
    newTerrain = room.getTile(limit(x2, 0, roomWidth-1), limit(y2, 0, roomLength-1)).getTerrain()
    if newTerrain in solid:
#     if self.getName() != 'player': #uncomment to walk through walls
      return False
    enemy = creatures.findAt(self.pos['z'], self.pos['levelX'], self.pos['levelY'], x2, y2)
    if enemy != None:
      #if self.attack(enemy): return True
      enemy.takeDamage(1) #TODO different amounts of damage, only attack enemies
      return True #return it
    #if moving diagonally and standing on a door or attempting to move on to one
    if dx != 0 and dy != 0 and DOOR_ID in [terrain, newTerrain]:
      return False
    self.pos['roomX'] = x2
    self.pos['roomY'] = y2
    if self.pos['roomX']<0 and self.pos['levelX']>0:
      self.pos['levelX']-=1
      oldRoomLength = roomLength
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      self.pos['roomX']=roomWidth-1
      if not roomLength == oldRoomLength: self.pos['roomY'] = int(roomLength/2)
    elif self.pos['roomX']>roomWidth-1 and self.pos['levelX']<levelWidth-1:
      self.pos['levelX']+=1
      oldRoomLength = roomLength
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      self.pos['roomX']=0
      if not roomLength == oldRoomLength: self.pos['roomY'] = int(roomLength/2)
    elif self.pos['roomY']<0 and self.pos['levelY']>0:
      self.pos['levelY']-=1
      oldRoomWidth = roomWidth
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      if not roomWidth == oldRoomWidth: self.pos['roomX'] = int(roomWidth/2)
      self.pos['roomY']=roomLength-1
    elif self.pos['roomY']>roomLength-1 and self.pos['levelY']<levelLength-1:
      self.pos['levelY']+=1
      oldRoomWidth = roomWidth
      room, roomWidth, roomLength = level.loadRoom(self.pos['levelX'], self.pos['levelY'])
      if not roomWidth == oldRoomWidth: self.pos['roomX'] = int(roomWidth/2)
      self.pos['roomY']=0
    self.pos['roomX'] = limit(self.pos['roomX'], 0, roomWidth-1)
    self.pos['roomY'] = limit(self.pos['roomY'], 0, roomLength-1)
    return True

class Monster(Creature):
  def setType(self, type):
    self.type = type
    self.name = monsters[type]['name']
    self.char = monsters[type]['char']
    self.color = monsters[type]['color']
    self.maxHealth = monsters[type]['HP']
    self.health = self.maxHealth
  def getChar(self): return self.char
  def getName(self): return self.name
  def getColor(self): return self.color
  def act(self, creatures): #TODO monsters get stuck in doors
    #TODO remember where the player was last seen and navigate there even if it is in a different room
    player = creatures.getPlayer()
    x1 = self.pos['levelX']
    y1 = self.pos['levelY']
    playerPos = player.getPos()
    x2 = playerPos['levelX']
    y2 = playerPos['levelY']
    if x1 != x2 or y1 != y2:
      for i in range(10): 
        if self.wander(creatures): return True
      return True;
    x1 = self.pos['roomX']
    y1 = self.pos['roomY']
    x2 = playerPos['roomX']
    y2 = playerPos['roomY']
    dx = dy = 0
    if x2>x1: dx=1
    if x2<x1: dx=-1
    if y2>y1: dy=1
    if y2<y1: dy=-1
    terrain = self.getRoom().getTile(self.pos['roomX'], self.pos['roomY']).getTerrain()
    if terrain == UP_STAIRS_ID: self.goUp()
    elif terrain == DOWN_STAIRS_ID: self.goDown()
    else:self.move(dx, dy, creatures)
    return True

class Player(Creature):
  def getChar(self):  return PLAYER_ID
  def getColor(self): return PLAYER_COLOR
  def raycast(self): 
    startX = self.pos['roomX']
    startY = self.pos['roomY']
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
    dx = (-1, 0, 1, 1,  1,  0, -1, -1)
    dy = ( 1, 1, 1, 0, -1, -1, -1,  0)
    for i in range(8):
      if key == moveOpts[i][2]: return self.move(dx[i], dy[i], creatures) #TODO arrows/wasd double press controls
    terrain = room.getTile(self.pos['roomX'], self.pos['roomY']).getTerrain()
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
            pos = newPos(z, levelX, levelY, roomX, roomY)
            monster = Monster(levelset, pos, 0)
            monster.setType(random.randrange(8))
            self.creatures.append(monster)
    log(4, 'Added '+str(len(self.creatures)-1)+' monsters.')
  def getList(self): return self.creatures
  def getPlayer(self): return self.creatures[0]
  def getStatsString(self):
    stats = 'Creatures: '
    for c in self.creatures:
      stats += '['+chars[c.getChar()]+', '+c.getName()+', HP:'+str(c.getHealth())+'/'+str(c.getMaxHealth())+']'
    return stats
  def removeDead(self): # Bring out your dead!
    #rebuild the list, excluding creatures that return false for isAlive()
    self.creatures = [creature for creature in self.creatures if creature.isAlive()]
  def act(self):
    self.removeDead()
    playerZ = self.getPlayer().getPos()['z']
    for creature in self.creatures[1:]: #loop over a copy of creatures that excludes the 1st item (the player)
    #the copy also keeps it from messing up if one dies
      if creature.getPos()['z'] != playerZ:continue #only creatures on the same level as the player get to act
#      if creature.getPos()['z'] - playerZ <= 1:continue #only creatures near the same level as the player get to act
      creature.healthAct() #let each creature autoheal
      creature.act(self) #tell each creature to do its thing
      self.removeDead() #if it or any other creature died while on its turn, remove it
    return True
  def findAt(self, z, levelX, levelY, roomX, roomY):
    for creature in self.creatures:
      pos = creature.getPos()
      if pos['z'] != z:continue
      if pos['levelX'] != levelX:continue
      if pos['levelY'] != levelY:continue
      if pos['roomX'] != roomX:continue
      if pos['roomY'] != roomY:continue
      return creature
    return None

def display(screen, creatures):
#  displayStartTime = time.time()
  player = creatures.getPlayer()
  pos = player.getPos()
  z = pos['z']
  levelX = pos['levelX']
  levelY = pos['levelY']
  roomX = pos['roomX']
  roomY = pos['roomY']

  level = player.getLevel()
  room = level.getRoom(levelX, levelY)
  roomWidth, roomLength = room.getWL()
  levelWidth, levelLength = level.getWL()

  screen.clear()
  #TODO improve status bar
  #  creatureStats = creatures.getStatsString()
  line1 = player.getName()+'  '+level.getName()
  screen.addstr(1,0,line1)
  player.displayHP(screen, 1,len(line1)+2)

  roomDispX = levelWidth*5+3
  roomDispY = 5
  #                       h,l,y,x
  miniWin = curses.newwin(levelLength*3+2, levelWidth*5+2, roomDispY, 0)
#  miniWin.clear()
  miniWin.border()

  minimap = Minimap(level)

  for x, y in doublerange(levelWidth, levelLength):
    miniroom = minimap.getMiniroom(x, y)
    if miniroom.isShown():
      middle=miniroom.getMiddle()
      color=miniroom.getColor()
      if x==levelX and y==levelY:
        middle=player.getChar()
        color = PLAYER_COLOR
      miniWin.addstr(2+y*3,2+x*5, '[ ]')
      miniWin.addch(2+y*3,3+x*5, chars[middle], curses.color_pair(color))
      doors = miniroom.getDoors()
      visible = miniroom.getVisibleWalls()
      char = ''
      if not visible['north']: char = '?'
      elif doors['north']: char = '|'
      else: char = ' '
      miniWin.addch(1+y*3,3+x*5, char)

      if not visible['south']: char = '?'
      elif doors['south']: char = '|'
      else: char = ' '
      miniWin.addch(3+y*3,3+x*5, char)

      if not visible['west']: char = '?'
      elif doors['west']: char = '-'
      else: char = ' '
      miniWin.addch(2+y*3,1+x*5, char)

      if not visible['east']: char = '?'
      elif doors['east']: char = '-'
      else: char = ' '
      miniWin.addch(2+y*3,5+x*5, char)

  #TODO BUG fix the room window needing 1 extra length/width (roomWidth+1)
  roomWin = curses.newwin(roomLength, roomWidth+1, roomDispY, roomDispX)
#  roomWin.border()

  for x, y in doublerange(roomWidth, roomLength):
    tile = room.getTile(x, y)
    char = tile.getTerrain()
    color = tile.getColor()
    if not tile.isShown(): char = color = 0

    roomWin.addch(y,x,chars[char], curses.color_pair(color))
  for creature in reversed(creatures.getList()):
    pos = creature.getPos()
    if pos['z'] != z: continue
    if pos['levelX'] != levelX: continue
    if pos['levelY'] != levelY: continue
    char = creature.getChar()
    color = creature.getColor()
    roomWin.addch(pos['roomY'],pos['roomX'],chars[char],
            curses.color_pair(color)+curses.A_REVERSE*creature.isInverted())

  screen.noutrefresh() #mark each screen for refresh but wait
  roomWin.noutrefresh()
  miniWin.noutrefresh()
  curses.doupdate() #refresh all screens at the same time
  screen.move(roomDispY+roomY, roomDispX+roomX) #move the cursor to the player
#  log(1, 'Display time', time.time() - displayStartTime)

#TODO improve options
#TODO save options in each save file and have options file
#TODO arrow keys double press controls (or wasd double press)
def optionsMenu():
  quit = False
  #                   h,  l,  y, x
  win = curses.newwin(19, 27, 0, 0)
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
        moveOpts[i][1] = ('1','2','3','6','9','8','7','4')[i]
        moveOpts[i][2] = ('1','2','3','6','9','8','7','4')[i]
    elif key=='2':
      moveOpts[9][3] = False
      moveOpts[10][3] = True
      moveOpts[11][3] = False
      for i in range(8):
        moveOpts[i][1] = ('1','v','3','>','9','^','7','<')[i]
        moveOpts[i][2] = ('1','KEY_DOWN','3','KEY_RIGHT','9','KEY_UP','7','KEY_LEFT')[i]
    elif key=='3':
      moveOpts[9][3] = False
      moveOpts[10][3] = False
      moveOpts[11][3] = True
      for i in range(8):
        moveOpts[i][1] = ('Z','X','C','D','E','W','Q','A')[i]
        moveOpts[i][2] = ('z','x','c','d','e','w','q','a')[i]
    #                enter key    spacebar
    elif key=='q' or key=='\n' or key== ' ': quit = True
  return moveOpts

def textField(screen, y, x, prompt, sizeLimit): #TODO move left and right in text fields
  screen.addstr(y,x,prompt)
  x += len(prompt)
  text=result=key=''
  while True:
    key=screen.getkey()
#    log(1, 'key pressed', key)
#    if len(key)==1: log(1, 'key code', ord(key))
    if key=='\n':
      result = text
      break
    if len(key)==1 and ord(key)==27: break #ESC key
    if key=='KEY_BACKSPACE':
      if len(text)==0: break
      text=text[:-1]
      screen.addch(y,x+len(text),' ')
    elif len(text) < sizeLimit: text+=key
    screen.addstr(y,x,text)
  return result

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

def deathMessage(screen):
  #                   h,  l,  y, x
  win = curses.newwin(4,  17, 0, 6)
  win.border()
  win.addstr(1,4,'You Died!') #TODO improve player death message
  win.addstr(2,1,'Press q to quit')
  win.refresh()
  key = ' '
  while key != 'q': key = screen.getkey()

def saveGame(saveFilePath, screen, creatures):
  screen.addstr(0,0,"Saving game...")
  screen.refresh()
  file = gzip.open(saveFilePath,'wb')
  pickle.dump(creatures, file)
  file.close()
  log(10, 'Game saved at', saveFilePath)

def loadGame(saveFilePath, screen):
  screen.addstr(0,0,"Loading save file...")
  screen.refresh()
  file = gzip.open(saveFilePath,'rb')
  creatures = pickle.load(file)
  player = creatures.getPlayer()
  levelset = player.getLevelset()
  log(10, 'Game loaded from', saveFilePath)
  os.remove(saveFilePath)
  return levelset, player, creatures

#TODO add levels when they are reached instead of all at startup
def newGame(screen, height, creatureFrequency, playerName):
  screen.addstr(0,0,"Please wait a moment while I dig the dungeon...")
  screen.refresh()
  startTime = time.time()
  #good layout: level:6x3 room:13x11 or 15x11
  levelset = randomLevelset(height)
  player = Player(levelset, levelset.getStartingPos(), 100)
  player.setName(playerName)
  player.setInverted(True)

  #generate the monsters
  creatures = Creatures(levelset, creatureFrequency, player)
  log(20, 'Game creation time', time.time() - startTime)
  return levelset, player, creatures

def saveMenu(saveFilePath, screen, creatures):
  screen.addstr(0,0,"Really save and quit? (y/n)")
  screen.refresh()
  if screen.getkey() in ['y', 'Y']:
    screen.addstr(0,0,"                           ") #clear the prompt message
    saveGame(saveFilePath, screen, creatures)
    return True
  return False

def main(screen):
#TODO catch KeyboardInterrupt exceptions and save/quit
  screen.clear() #Clear terminal screen
  initializeChars()
  curses.curs_set(2) #set cursor to block mode

  if not os.path.exists(saveGameDir):
    os.makedirs(saveGameDir)
    
  log(1000, '==== Quest Log File ====') #TODO rename the game

  saveFiles = os.listdir(saveGameDir)

  log(3, 'Games will be saved in', saveGameDir)
  log(3, 'Save Files', saveFiles)

  playerName = ''
  if len(sys.argv)==2:
    playerName = sys.argv[1]
  else:
    while len(playerName)==0: playerName = textField(screen, 5,0, 'What is your name? ', 60)
  log(5, 'Player Name', playerName)

  saveFilePath = os.path.join(saveGameDir, playerName+'.save')
  log(5, 'Save file path', saveFilePath)

  levelset = None
  player = None
  creatures = None

  if playerName+'.save' in saveFiles:
    log(5, playerName+' has a save file.')
    levelset, player, creatures = loadGame(saveFilePath, screen)
  else:
    log(5, playerName+' does not have a save file.')
    levelset, player, creatures = newGame(screen, 50, 0.01, playerName) #TODO use multithreading to hide the create game lag

  while True:
    if not player.isAlive():
      deathMessage(screen)
      return
    player.raycast()
    display(screen, creatures)
    key = screen.getkey()
    player.healthAct()
    while not player.act(creatures, key):
      if key == 'S':
        if saveMenu(saveFilePath, screen, creatures): return
        else: display(screen, creatures)
      if key == 'o':
        optionsMenu()
        display(screen, creatures)
      elif key == '#':
        command = textField(screen, 0,0, '# ', 60)
        log(10, "Extended Command", command)
        if command=='quit': return
        display(screen, creatures)
      key = screen.getkey()
    creatures.act()

curses.wrapper(main)

# 	DONE:
# test on windows
# save game
# creature colors
# add constants
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
