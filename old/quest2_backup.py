#!/usr/bin/python
import os, random, math, time, curses, sys

startTime = time.time()
#chars = '.#^v!Os-*:++;[???---////TT(r)?[[[]]]]?ooooo???????'

#        000000_0000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999
#        012345_67890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
chars = ' .#/=\\|@<>'
#these are the types of terrain and items

solid = [2,3,4,5,6] #cannot move through
opaque = [2,3,4,5,6] # cannoth see through

logfile = 'quest_log.txt'

#clear the logfile
#file = open(logfile, 'w')
#file.write("==== Quest Log File ====\n")
#file.close()

#writes a line to the logfile
def log(text):
  file = open(logfile, 'a')
  file.write(str(text) + '\n')
  file.close()

#restricts the imput to be between min and max
def limit(value, minval, maxval):
  return min(maxval, max(minval, value))

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
  def setTerrain(self, terrainID):
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

class Doors:
  'Stores info about which of the 4 directions are active'
  def __init__(self, left, right, top, bottom):
    self.setLeft(left)
    self.setRight(right)
    self.setTop(top)
    self.setBottom(bottom)
  def getLeft(self):
    return self.left
  def getRight(self):
    return self.right
  def getTop(self):
    return self.top
  def getBottom(self):
    return self.bottom
  def setLeft(self, left):
    self.left = left
  def setRight(self, right):
    self.right = right
  def setTop(self, top):
    self.top = top
  def setBottom(self, bottom):
    self.bottom = bottom
  def getInverse(self):
    return Doors(self.right, self.left, self.bottom, self.top)
  def add(self, doors):
    self.left = self.left or doors.left
    self.right = self.right or doors.right
    self.top = self.top or doors.top
    self.bottom = self.bottom or doors.bottom

class Room:
  'Contains one room of a level and all the monsters and objects in it.'
  def __init__(self, width, length): #create a new room
    self.doors = Doors(False, False, False, False)
    #minimum dimensions are 3x3
    if width<3: width = 3
    if length<3: length = 3
    #store the width and length
    self.width = width
    self.length = length
    #template defines the smallest room
    template = [
    [3,4,5],
    [6,1,6],
    [5,4,3]
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
    self.doors.add(doors)
    for y in range(self.length):
      for x in range(self.width):
        if doors.getLeft()   and abs(y-(self.length-1)/2.0)<1 and x==0 \
        or doors.getRight()  and abs(y-(self.length-1)/2.0)<1 and x==self.width-1\
        or doors.getTop()    and abs(x-(self.width -1)/2.0)<1 and y==0 \
        or doors.getBottom() and abs(x-(self.width -1)/2.0)<1 and y==self.length-1:
          self.getTile(x, y).setTerrain(1)
  def populate(self, density, char):
    for y in range(self.length):
      for x in range(self.width):
        tile = self.getTile(x, y)
        if tile.getTerrain() == 1 and random.random() < density: tile.setTerrain(char)

  def getDoors(self):
    return self.doors
  def invert(self):
    for y in range(self.length):
      for x in range(self.width):
        self.getTile(x, y).hide()
  def raycast(self, startX, startY):
    direction = 0
    self.getTile(startX, startY).show()
    while direction < 2*math.pi:
      x=startX
      y=startY
      walls = 0
      while walls < 1:
        x+=math.cos(direction)
        y+=math.sin(direction)
        xint = int(x+.5)
        yint = int(y+.5)
        if xint >= self.width or yint >= self.length or xint < 0 or yint < 0:
          char = 2
        else:
          tile = self.getTile(int(x), int(y))
          tile.show()
          char = tile.getTerrain()
        if char in opaque: walls += 1
      direction += .01*math.pi

class Miniroom:
  def __init__(self, shown, middle, doors):
    self.shown = shown
    self.middle = middle
    self.doors = doors
  def isShown(self):
    return self.shown
  def getMiddle(self):
    return self.middle
  def setMiddle(self, middle):
    self.middle = middle
  def getDoors(self):
    return self.doors

#class Minimap:
#  def __init__(self, minimap):
#    self.minimap = minimap
#  def getMiniroom(self, x, y):
#    return self.minimap[y][x]

class Level:
  'Contains a 2-D list of rooms'
  def __init__(self, width, length, minRoomWidth, maxRoomWidth, minRoomLength, maxRoomLength):
    self.width = width
    self.length = length
    self.level = []
    for y in range(length):
      row = []
      for x in range(width):
        roomWidth = random.randint(minRoomWidth, maxRoomWidth)
        roomLength = random.randint(minRoomLength, maxRoomLength)
        room = Room(roomWidth, roomLength)
        row.append(room)
      self.level.append(row)
  def getWL(self):
    #return the dimensions
    return self.width, self.length
  def getRoom(self, x, y):
    return self.level[y][x]
  def checkForConnection(self, minimap, x, y, fill, lookFor):
    miniroom = minimap[y][x]
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
  def addStairs(self):
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
    upRoom.getTile(int(upWidth/2), int(upLength/2)).setTerrain(8)
    downRoom.getTile(int(downWidth/2), int(downLength/2)).setTerrain(9)
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
        doors.left = True
      elif i==1:
        x2+=1
        doors.right = True
      elif i==2:
        y2-=1
        doors.top = True
      elif i==3:
        y2+=1
        doors.bottom = True
      doors2 = doors.getInverse()
      if x2>=0 and x2<self.width and y2>=0 and y2<self.length:
        self.getRoom(x, y).addDoors(doors)
        self.getRoom(x2, y2).addDoors(doors2)
        minimap = self.getMinimap()
        for x in range(self.width):
          for y in range(self.length):
            minimap[y][x].setMiddle(0)
        minimap[downY][downX].setMiddle(2)
        connected = self.checkForConnection(minimap, upX, upY, 1, 2)
  def findStairs(self, up):
    char = 9
    if up: char = 8
    return self.findChar(char)
  def findChar(self, char):
    for y in range(self.length):
      for x in range(self.width):
        room = self.getRoom(x, y)
        roomWidth, roomLength = room.getWL()
        for y2 in range(roomLength):
          for x2 in range(roomWidth):
            if room.getTile(x2, y2).getTerrain()==char: return x, y, x2, y2
    return 0,0,0,0
  def invert(self):
    for x in range(self.width):
      for y in range(self.length):
        self.getRoom(x, y).invert()
  def getMinimap(self):
    minimap = []
    for y in range(self.length):
      row = []
      for x in range(self.width):
        shown = False
        room = self.getRoom(x, y)
        roomWidth, roomLength = room.getWL()
        for y2 in range(roomLength):
          for x2 in range(roomWidth):
            if room.getTile(x2, y2).isShown(): shown = True
        middle = 0
        for y2 in range(roomLength):
          for x2 in range(roomWidth):
            terrain = room.getTile(x2, y2).getTerrain()
            if terrain == 8: middle=8
            if terrain == 9: middle=9
        doors = room.getDoors()
        row.append(Miniroom(shown, middle, doors))
      minimap.append(row)
    return minimap
  def loadRoom(self, levelX, levelY):
    room = self.getRoom(levelX, levelY)
    roomWidth, roomLength = room.getWL()
    return room, roomWidth, roomLength

class Levelset:
  def __init__(self, height, type):
    self.height = height
    self.levelset = []
    for i in range(height):
      levelWidth = random.randint(3,7)
      levelheight = random.randint(3,5)
      minRoomWidth = random.randint(5,10)
      maxRoomWidth = minRoomWidth + random.randint(3,6)
      minRoomLength = random.randint(4,9)
      maxRoomLength = minRoomLength + random.randint(2,5)
      level = Level(levelWidth, levelheight, minRoomWidth, maxRoomWidth, minRoomLength, maxRoomLength)
      level.addStairs()
      level.invert()
      self.levelset.append(level)
  def getLevel(self, i):
    return self.levelset[i]
  def loadLevel(self, i, upStairs):
    level = self.getLevel(i)
    levelWidth, levelLength = level.getWL()
    levelX, levelY, roomX, roomY = level.findStairs(upStairs)
#    levelX, levelY, roomX, roomY = 1,1,1,1
    room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
    return level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY

#class Player:
#  def __init__(self):
#  def move(self, roomX, roomY, dx, dy, room):

def move(roomX, roomY, dx, dy, room):
  roomWidth, roomLength = room.getWL()
  x2=roomX+dx
  y2=roomY+dy
  if dx==0 and dy==0 or \
  x2<-1 or x2>roomWidth or \
  y2<-1 or y2>roomLength:
    return False, roomX, roomY
  if room.getTile(limit(x2, 0, roomWidth-1), limit(y2, 0, roomLength-1)).getTerrain() in solid:
    return False, roomX, roomY
  return True, x2, y2

def display(screen, room, roomX, roomY, level, levelX, levelY):
  roomWidth, roomLength = room.getWL()
  levelWidth, levelLength = level.getWL()

  roomDispX = levelWidth*5+2
  roomDispY = 10

  screen.clear()
  screen.addstr(1,0,'Stats', curses.A_REVERSE)
  minimap = level.getMinimap()

  for y in range(levelLength):
    for x in range(levelWidth):
      miniroom = minimap[y][x]
      if miniroom.isShown():
        middle=miniroom.getMiddle()
        if x==levelX and y==levelY: middle=7
        screen.addstr(roomDispY+y*3,2+x*5, '['+chars[middle]+']')
        doors = miniroom.getDoors()
        if doors.getTop() and y>0: screen.addstr(roomDispY-1+y*3,3+x*5, '|')
        if doors.getBottom() and y<levelLength-1: screen.addstr(roomDispY+1+y*3,3+x*5, '|')
        if doors.getLeft() and x>0: screen.addstr(roomDispY+y*3,1+x*5, '-')
        if doors.getRight() and x<levelWidth-1: screen.addstr(roomDispY+y*3,5+x*5, '-')

  for y in range(roomLength):
    row = ''
    for x in range(roomWidth):
      tile = room.getTile(x, y)
      char = tile.getTerrain()
      if x==roomX and y==roomY: char = 7
      if not tile.isShown(): char = 0
      row += chars[char]
    screen.addstr(roomDispY+y,roomDispX,row)
  screen.move(roomDispY+roomY, roomX+roomDispX)

def optionsMenu(screen, options):
  quit = False
  winx = 0
  winy = 0
  winwidth = 27
  winheight = 20
  win = curses.newwin(winheight,winwidth,winx,winy)
  while not quit:
    win.clear()
    win.addstr(0,0,'='*winwidth)
    win.addstr(1,7,'Options')
    for y in range(1,winheight-1):
      win.addstr(y,0,'|')
      i=y-3
      if i>=0 and i<len(options):
        win.addstr(y,2,options[i][0])
        win.addstr(y,14,options[i][1], options[i][2]*curses.A_REVERSE)
      win.addstr(y,winwidth-1,'|')
    win.addstr(y-1,4,'Press q to quit')
    win.addstr(y,0,'='*winwidth)
    key = win.getkey()
    win.addstr(1,1,key)
    win.refresh()

    if key=='1':
      options[9][2] = True
      options[10][2] = False
      options[11][2] = False
      for i in range(8):
        options[i][1] = ['1','2','3','6','9','8','7','4'][i]
    elif key=='2':
      options[9][2] = False
      options[10][2] = True
      options[11][2] = False
      for i in range(8):
        options[i][1] = ['1','KEY_DOWN','3','KEY_RIGHT','9','KEY_UP','7','KEY_LEFT'][i]
    elif key=='3':
      options[9][2] = False
      options[10][2] = False
      options[11][2] = True
      for i in range(8):
        options[i][1] = ['z','x','c','d','e','w','q','a'][i]
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
      screen.addstr(0,len(command),' ')
      if command=='': return ''
    else:
      command+=key
    screen.addstr(0,0,command)
    key=screen.getkey()
  return command




def main(screen):
  screen.clear() #Clear terminal screen
  
  #movement key options
  options = [
  ['South-West ', '1', True],
  ['South      ', '2', True],
  ['South-East ', '3', True],
  ['East       ', '6', True],
  ['North-East ', '9', True],
  ['North      ', '8', True],
  ['North-West ', '7', True],
  ['West       ', '4', True],
  ['           ', ' ', False],
  ['Press 1 for', 'numpad', True],
  ['Press 2 for', 'arrows+1379', False],
  ['Press 3 for', 'QWEASDZXC', False]
  ]

  height = 1000 #random.randint(2,3)
  levelset = Levelset(height, 0)
  z = 0
  level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY = levelset.loadLevel(z, True)

  log(time.time()-startTime)
  dx = dy = 0
  while True:
    room.raycast(roomX, roomY)
    display(screen, room, roomX, roomY, level, levelX, levelY)
    screen.refresh()
    moved = False
    while not moved:
      key = screen.getkey()
      dx=0; dy=0
      if   key == options[0][1]: dx=-1; dy= 1
      elif key == options[1][1]: dx= 0; dy= 1
      elif key == options[2][1]: dx= 1; dy= 1
      elif key == options[3][1]: dx= 1; dy= 0
      elif key == options[4][1]: dx= 1; dy=-1
      elif key == options[5][1]: dx= 0; dy=-1
      elif key == options[6][1]: dx=-1; dy=-1
      elif key == options[7][1]: dx=-1; dy= 0
      elif key == '<':
        if room.getTile(roomX, roomY).getTerrain() == 8 and z > 0:
          z-=1
          level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY = levelset.loadLevel(z, False)
          moved = True
      elif key == '>':
        if room.getTile(roomX, roomY).getTerrain() == 9 and z < height-1:
          z+=1
          level, levelWidth, levelLength, levelX, levelY, room, roomWidth, roomLength, roomX, roomY = levelset.loadLevel(z, True)
          moved = True
      elif key == 'o':
        options = optionsMenu(screen, options)
        display(screen, room, roomX, roomY, level, levelX, levelY)
        screen.refresh()
      elif key == '#':
        command = extendedCommand(screen)
        if command=='#quit': return
        display(screen, room, roomX, roomY, level, levelX, levelY)
        screen.refresh()
      if not moved: moved, roomX, roomY = move(roomX, roomY, dx, dy, room)
    if roomX<0 and levelX>0:
      levelX-=1
      #oldRoomlength = roomLength
      room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
      roomX=roomWidth-1
      roomY = int(roomLength/2)
    elif roomX>roomWidth-1 and levelX<levelWidth-1:
      levelX+=1
      #oldRoomlength = roomLength
      room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
      roomX=0
      roomY = int(roomLength/2)
    elif roomY<0 and levelY>0:
      levelY-=1
      room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
      roomX = int(roomWidth/2)
      roomY=roomLength-1
    elif roomY>roomLength-1 and levelY<levelLength-1:
      levelY+=1
      room, roomWidth, roomLength = level.loadRoom(levelX, levelY)
      roomX = int(roomWidth/2)
      roomY=0
    roomX = limit(roomX, 0, roomWidth-1)
    roomY = limit(roomY, 0, roomLength-1)

curses.wrapper(main)
