#!/usr/bin/python
import os, random, math, time, curses, sys

logfile = 'quest_log.txt'

file = open(logfile, 'w')
file.write("==== Quest Log File ====\n")
file.close()


#chars = '.#^v!Os-*:++;[???---////TT(r)?[[[]]]]?ooooo???????'

#        000000_0000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999
#        012345_67890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
chars = ' .#/=\\|@<>'
pi = math.pi

solid = [2,3,4,5,6]

opaque = [2,3,4,5,6]

def log(text):
  file = open(logfile, 'a')
  file.write(str(text) + '\n')
  file.close()

def limit(value, minval, maxval):
  return min(maxval, max(minval, value))

def getWL(room):
  return len(room[0]), len(room)

def invert(list2D):
  return [[-x for x in y] for y in list2D]

def invertLevel(level):
  levelWidth, levelLength = getWL(level)
  for x in range(levelWidth):
    for y in range(levelLength):
      level[y][x] = invert(level[y][x])
  return level

def makeRoom(width, length):
  borders = [
  [3,4,5],
  [6,1,6],
  [5,4,3]
  ]
  if width<1: width = 1
  if length<1: length = 1
  room = []
  for y in range(length):
    row = []
    for x in range(width):
      row.append(borders[(y>0)+(y==length-1)][(x>0)+(x==width-1)])
    room.append(row)
  return room

def addDoors(room, inverted, doors):
  #doors: [left, right, top, bottom]
  width, length = getWL(room)
  sign = 1
  if inverted: sign = -1

  for y in range(length):
    for x in range(width):
      val = room[y][x]
      if doors[0] and abs(y-(length-1)/2.0)<1 and x==0 \
      or doors[1] and abs(y-(length-1)/2.0)<1 and x==width-1\
      or doors[2] and abs(x-(width -1)/2.0)<1 and y==0 \
      or doors[3] and abs(x-(width -1)/2.0)<1 and y==length-1:
        room[y][x] = sign
  return room

def populateRoom(room, density):
  width, length = getWL(room)
  for y in range(length):
    for x in range(width):
      if room[y][x] == 1 and random.random() < density: room[y][x] = 2
  return room

def getConnections(room):
  width, length = getWL(room)
  left = right = top = bottom = False
  for x in range(width):
    if room[0][x] == 1: top=True
    if room[length-1][x] == 1: bottom=True
  for y in range(length):
    if room[y][0] == 1: left=True
    if room[y][width-1] == 1: right=True
  return left, right, top, bottom  

def makeLevel(width, length, minRoomWidth, maxRoomWidth, minRoomLength, maxRoomLength):
  level = []
  for y in range(length):
    row = []
    for x in range(width):
      roomWidth = random.randint(minRoomWidth, maxRoomWidth)
      roomLength = random.randint(minRoomLength, maxRoomLength)
      room = makeRoom(roomWidth, roomLength)
#      room = populateRoom(room, 0.3)
#      room = invert(room)
#      room = addDoors(room, 1, [1,1,1,1])
      row.append(room)
    level.append(row)
  return level

def checkForConnection(minimap, x, y, fill, lookFor):
  miniroom = minimap[y][x]
  #log(miniroom)
  if miniroom[0] == fill: return False
  if miniroom[0] == lookFor: return True
  miniroom[0] = fill
  if miniroom[2]:
    if checkForConnection(minimap, x-1, y, fill, lookFor): return True
  if miniroom[3]:
    if checkForConnection(minimap, x+1, y, fill, lookFor): return True
  if miniroom[4]:
    if checkForConnection(minimap, x, y-1, fill, lookFor): return True
  if miniroom[5]:
    if checkForConnection(minimap, x, y+1, fill, lookFor): return True
  return False  

def addStairs(level):
  levelWidth, levelLength = getWL(level)
  upX = random.randrange(levelWidth)
  upY = random.randrange(levelLength)
  downX = upX
  downY = upY
  while upX==downX and upY==downY:
    downX = random.randrange(levelWidth)
    downY = random.randrange(levelLength)
  upRoom = level[upY][upX]
  downRoom = level[downY][downX]
  upWidth, upLength = getWL(upRoom)
  downWidth, downLength = getWL(downRoom)
  level[upY][upX][int(upLength/2)][int(upWidth/2)] = 8
  level[downY][downX][int(downLength/2)][int(downWidth/2)] = 9
  connected = False
  while not connected:
    doors = [0,0,0,0]
    doors2 = [0,0,0,0]
    i = random.randrange(4)
    doors[i] = 1
    x = random.randrange(levelWidth)
    y = random.randrange(levelLength)
    doors2 = [doors[1], doors[0], doors[3], doors[2]]
    x2=x
    y2=y
    if   i==0: x2-=1
    elif i==1: x2+=1
    elif i==2: y2-=1
    elif i==3: y2+=1
    if x2>=0 and x2<levelWidth and y2>=0 and y2<levelLength:
      level[y][x] = addDoors(level[y][x], 0, doors)
      level[y2][x2] = addDoors(level[y2][x2], 0, doors2)
      minimap = getMinimap(level)
      for x in range(levelWidth):
        for y in range(levelLength):
          minimap[y][x][0] = 0
      minimap[downY][downX][0] = 2
      connected = checkForConnection(minimap, upX, upY, 1, 2)
  return level

def findStairs(level, up):
  levelWidth, levelLength = getWL(level)
  char = 9
  if up: char = 8
  for y in range(levelLength):
    for x in range(levelWidth):
      room = level[y][x]
      width, length = getWL(room)
      for y2 in range(length):
        for x2 in range(width):
          if abs(room[y2][x2])==char: return x, y, x2, y2
  return 0,0,0,0

def loadRoom(level, levelx, levely):
  room = level[levely][levelx]
  width, length = getWL(room)
  return room, width, length

def loadLevel(levelset, z, upStairs):
  level = levelset[z]  
  levelWidth, levelLength = getWL(level)
  levelx, levely, playerx, playery = findStairs(level, upStairs)
  room, width, length = loadRoom(level, levelx, levely)
  return level, levelWidth, levelLength, levelx, levely, room, width, length, playerx, playery

def getMinimap(level):
  levelWidth, levelLength = getWL(level)
  minimap = []
  for y in range(levelLength):
    row = []
    for x in range(levelWidth):
      show = False
      room = level[y][x]
      width, length = getWL(room)
      for y2 in range(length):
        for x2 in range(width):
          if room[y2][x2] > 0: show = True
      middle = 0
      for y2 in range(length):
        for x2 in range(width):
          if room[y2][x2] == 8: middle=8
          if room[y2][x2] == 9: middle=9
      left, right, top, bottom, = getConnections(room)
      row.append([show, middle, left, right, top, bottom])
    minimap.append(row)
  return minimap

def display(room, screen, playerx, playery, level, levelx, levely):
  width, length = getWL(room)
  levelWidth, levelLength = getWL(level)

  roomDispX = levelWidth*5+2
  roomDispY = 10

  screen.clear()
#  os.system('cls' if os.name == 'nt' else 'clear')
#  print(chr(27) + "[2J")
  screen.addstr(1,0,'Stats', curses.A_REVERSE)
#  print 'Stats' + '\n'
  minimap = getMinimap(level)

  for y in range(levelLength):
    for x in range(levelWidth):
      miniroom = minimap[y][x]
      show = miniroom[0]
      if show:
        middle=miniroom[1]
        if x==levelx and y==levely: middle=7
        screen.addstr(roomDispY+y*3,2+x*5, '['+chars[middle]+']')
        left   = miniroom[2]
        right  = miniroom[3]
        top    = miniroom[4]
        bottom = miniroom[5]
        if top and y>0: screen.addstr(roomDispY-1+y*3,3+x*5, '|')
        if bottom and y<levelLength-1: screen.addstr(roomDispY+1+y*3,3+x*5, '|')
        if left and x>0: screen.addstr(roomDispY+y*3,1+x*5, '-')
        if right and x<levelWidth-1: screen.addstr(roomDispY+y*3,5+x*5, '-')

  for y in range(length):
    row = ''
    for x in range(width):
      if x==playerx and y==playery: char = 7
      else: char = room[y][x]
#      char = room[y][x]
      if char < 0: char = 0
      row += chars[char]
    screen.addstr(roomDispY+y,roomDispX,row)
#  screen.addstr(4+playery, playerx, chars[7])
#  screen.addstr(20,0,str(level))
  screen.move(roomDispY+playery, playerx+roomDispX)

def raycast(room, startx, starty):
  width, length = getWL(room)
  direction = 0
  room[starty][startx] = abs(room[starty][startx])
  while direction < 2*pi:
    x=startx
    y=starty
    walls = 0
    while walls < 1:
      x+=math.cos(direction)
      y+=math.sin(direction)
      xint = int(x+.5)
      yint = int(y+.5)
      if xint >= width or yint >= length or xint < 0 or yint < 0:
        char = 2
      else:
        char = abs(room[yint][xint])
        room[yint][xint] = char
      if char in opaque: walls += 1
    direction += .01*pi
  return room

def move(playerx, playery, dx, dy, room):
  width, length = getWL(room)
  x2=playerx+dx
  y2=playery+dy
  if dx==0 and dy==0 or \
  x2<-1 or x2>width or \
  y2<-1 or y2>length:
    return False, playerx, playery
#  if x2>=0 and x2<width and \
#     y2>=0 and y2<length and \
#     room[y2][x2] in solid:
#    return False, playerx, playery
  if room[limit(y2, 0, length-1)][limit(x2, 0, width-1)] in solid:
    return False, playerx, playery
  return True, x2, y2

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
    #              enter key    spacebar
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
  screen.clear() #Clear screen

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

  levelset = []
  height = random.randint(2,3)
  for i in range(height):
    levelWidth = random.randint(3,7)
    levelheight = random.randint(3,5)
    minRoomWidth = random.randint(5,10)
    maxRoomWidth = minRoomWidth + random.randint(3,6)
    minRoomLength = random.randint(4,9)
    maxRoomLength = minRoomLength + random.randint(2,5)
    level = makeLevel(levelWidth, levelheight, minRoomWidth, maxRoomWidth, minRoomLength, maxRoomLength)
    level = addStairs(level)
    level = invertLevel(level)
    levelset.append(level)

  z = 0

  level, levelWidth, levelLength, levelx, levely, room, width, length, playerx, playery = loadLevel(levelset, z, True)

  dx = dy = 0
  while True:
    room = raycast(room, playerx, playery)
    display(room, screen, playerx, playery, level, levelx, levely)
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
        if room[playery][playerx] == 8 and z > 0:
          z-=1
          level, levelWidth, levelLength, levelx, levely, room, width, length, playerx, playery = loadLevel(levelset, z, False)
          moved = True
      elif key == '>':
        if room[playery][playerx] == 9 and z < height-1:
          z+=1
          level, levelWidth, levelLength, levelx, levely, room, width, length, playerx, playery = loadLevel(levelset, z, True)
          moved = True
      elif key == 'o':
        options = optionsMenu(screen, options)
        display(room, screen, playerx, playery, level, levelx, levely)
        screen.refresh()
      elif key == '#':
        command = extendedCommand(screen)
        if command=='#quit': return
        display(room, screen, playerx, playery, level, levelx, levely)
        screen.refresh()
      if not moved: moved, playerx, playery = move(playerx, playery, dx, dy, room)
    if playerx<0 and levelx>0:
      levelx-=1
      room, width, length = loadRoom(level, levelx, levely)
      playerx=width-1
    elif playerx>width-1 and levelx<levelWidth-1:
      levelx+=1
      room, width, length = loadRoom(level, levelx, levely)
      playerx=0
    elif playery<0 and levely>0:
      levely-=1
      room, width, length = loadRoom(level, levelx, levely)
      playery=length-1
    elif playery>length-1 and levely<levelLength-1:
      levely+=1
      room, width, length = loadRoom(level, levelx, levely)
      playery=0
    playerx = limit(playerx, 0, width-1)
    playery = limit(playery, 0, length-1)

curses.wrapper(main)
