# imports
import pygame
import math
import random
from data import spritesheet as sp
import json

# initialise pygame
pygame.init()
# set the caption of the window
pygame.display.set_caption('Invasion of the Tacos')
# variables for the width and height of the game window
displayWidth = 1920
displayHeight = 1080
# set the game display
gameDisplay = pygame.display.set_mode(
    (displayWidth, displayHeight), pygame.FULLSCREEN)
# game clock
clock = pygame.time.Clock()

# RGB colour codes
black = (0, 0, 0)
greyBackground = (28, 36, 54)
white = (255, 255, 255)
appleRed = (190, 22, 34)
lightAppleRed = (239, 21, 37)
leafGreen = (34, 177, 76)
lightLeafGreen = (43, 232, 98)

# gamePaused - unused
gamePaused = False

# for menu
canPlayGame = False

# getting last time for variables that rely on time
lastFire = pygame.time.get_ticks()
lastSpawn = pygame.time.get_ticks()
lastHit = pygame.time.get_ticks()

# spawn cooldown - the time between each enemy spawn
spawnCooldown = 1500

# ui
# loads the heart icon spritesheet
heartSS = sp.Spritesheet('data\Sprites\AppleHeartSS.png')
heartImgs = []
# each image 48x56
rectsAt = [(0, 0, 48, 56), (48, 0, 48, 56)]
heartImgs = heartSS.images_at(rectsAt, black)

# loads the main menu image
menuImg = pygame.image.load('data\MenuImages\MenuScreen.png')


# player class
class Player:
    # crucial to classes - always executed when the player is initiated, used to assign values and other operations that are necessary when the object is created
    def __init__(self, x, y):
        # player coordinates
        self.x = int(x)
        self.y = int(y)

        # player pixel dimensions
        self.width = 60
        self.height = 70

        # load player sprites
        self.playerSS = sp.Spritesheet('data\Sprites\AppleCharacterSS.png')
        self.playerImgs = []
        self.rectsAt = [(0, 0, 60, 70), (60, 0, 60, 70),
                        (0, 70, 60, 70), (60, 70, 60, 70)]
        self.playerImgs = self.playerSS.images_at(self.rectsAt, black)

        self.playerDeathImg = pygame.image.load('data\Sprites\DeadApple.png')

        self.currentImg = self.playerImgs[0]

        # collision rect - invisible rectangle over player that detects collisions
        # it is bit smaller than players image size for player benefit
        self.rect = pygame.Rect(
            self.x, self.y, self.width - 10, self.height - 10)

        # player velocity as a vector2
        self.playerVelocity = pygame.math.Vector2(0, 0)

        # movement bools
        self.leftPressed = False
        self.rightPressed = False
        self.upPressed = False
        self.downPressed = False

        # facing direction
        self.facingDirection = "right"

        # collision bools
        self.hasCollidedLeft = False
        self.hasCollidedRight = False
        self.hasCollidedUp = False
        self.hasCollidedDown = False

        # player movement speed
        self.speed = 3

        # health
        self.maxHealth = 3
        self.currentHealth = self.maxHealth
        self.isDead = False
        self.hitCooldown = 750
        self.playerDead = False

        # death screen ui
        self.canDrawDeathScreen = False  # for timing the ui on death
        self.timedDeath = False  # this is so diedAt doesn't get set all the time

        # flash when hit variables
        self.lastFlash = pygame.time.get_ticks()
        self.shouldFlash = False
        self.canFlash = False
        self.flashCooldown = 75

        # score
        self.score = 0

        # waves variables
        self.enemiesSpawned = 0  # keep track of how many enemies have spawned
        self.enemiesKilled = 0  # keep track of how many enemies have been killed
        self.waveNumber = 1  # keep track of what wave you are on
        self.waveCompleted = False  # check if the current wave has been completed
        # this is so you wait a few seconds until the next wave
        self.timeWaveDone = pygame.time.get_ticks()

        # get wave data from json file -- initial
        self.waveData = open('data\WaveData.json')
        self.contents = self.waveData.read()  # reads entire file into a single string
        # turns contents into a dictionary
        self.data = json.loads(self.contents)
        self.data = self.data["WaveData"]  # get list of dictionary
        # get wave name
        self.waveName = self.data[self.waveNumber - 1]["WaveName"]
        # get amount to kill
        self.toKill = self.data[self.waveNumber - 1]["EnemiesToKill"]
        # get which enemy types can spawn during this wave
        self.enemyTypesForWave = self.data[self.waveNumber - 1]["EnemyTypes"]
        # get the weights for each enemy type that can spawn during this wave
        self.enemyWeightsForWave = self.data[self.waveNumber -
                                             1]["EnemyTypesWeights"]
        self.waveData.close()

    # draw the player's sprite to the screen - this is called once per frame
    def drawPlayer(self):
        # if not dead, draw character sprites
        if not self.playerDead:
            if self.facingDirection == "right" or self.facingDirection == "right up" or self.facingDirection == "right down":
                self.currentImg = self.playerImgs[0]
            elif self.facingDirection == "left" or self.facingDirection == "left up" or self.facingDirection == "left down":
                self.currentImg = self.playerImgs[1]
            elif self.facingDirection == "up":
                self.currentImg = self.playerImgs[2]
            elif self.facingDirection == "down":
                self.currentImg = self.playerImgs[3]
        # if dead, draw gravestone
        else:
            self.currentImg = self.playerDeathImg

        # blit draws the image to the screen at the player's coordinates
        gameDisplay.blit(self.currentImg, (self.x, self.y))

    # update calls every frame
    def update(self):
        # update rect position
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # self.playerVelocity[0] = x of vector
        # self.playerVelocity[1] = y of vector
        self.playerVelocity = pygame.math.Vector2(0, 0)

        # allow the player to move if they haven't collided with a wall
        if not self.hasCollidedLeft:
            if self.leftPressed and not self.rightPressed:
                self.playerVelocity[0] = -self.speed
                self.facingDirection = "left"

        if not self.hasCollidedRight:
            if self.rightPressed and not self.leftPressed:
                self.playerVelocity[0] = self.speed
                self.facingDirection = "right"

        if not self.hasCollidedUp:
            if self.upPressed and not self.downPressed:
                self.playerVelocity[1] = -self.speed
                self.facingDirection = "up"

        if not self.hasCollidedDown:
            if self.downPressed and not self.upPressed:
                self.playerVelocity[1] = self.speed
                self.facingDirection = "down"

        # diagonal fix - by normalising the vector
        if not self.hasCollidedLeft and not self.hasCollidedUp:
            if self.leftPressed and self.upPressed:
                self.playerVelocity[0] = -self.speed/math.sqrt(2)
                self.playerVelocity[1] = -self.speed/math.sqrt(2)
                self.facingDirection = "left up"

        if not self.hasCollidedLeft and not self.hasCollidedDown:
            if self.leftPressed and self.downPressed:
                self.playerVelocity[0] = -self.speed/math.sqrt(2)
                self.playerVelocity[1] = self.speed/math.sqrt(2)
                self.facingDirection = "left down"

        if not self.hasCollidedRight and not self.hasCollidedUp:
            if self.rightPressed and self.upPressed:
                self.playerVelocity[0] = self.speed/math.sqrt(2)
                self.playerVelocity[1] = -self.speed/math.sqrt(2)
                self.facingDirection = "right up"

        if not self.hasCollidedRight and not self.hasCollidedDown:
            if self.rightPressed and self.downPressed:
                self.playerVelocity[0] = self.speed/math.sqrt(2)
                self.playerVelocity[1] = self.speed/math.sqrt(2)
                self.facingDirection = "right down"

        self.x += self.playerVelocity[0]
        self.y += self.playerVelocity[1]

        # speed debug
        """print(str(self.playerVelocity[0]) +
              ", " + str(self.playerVelocity[1]))"""

        # flash anim
        if self.shouldFlash and self.canFlash:
            self.currentImg.set_alpha(64)
        else:
            self.currentImg.set_alpha(255)

        # if health is 0 or below (dead)
        if self.currentHealth <= 0:
            # pause the game
            self.playerDead = True
            if not self.timedDeath:
                self.diedAt = pygame.time.get_ticks()
                self.timedDeath = True

        # waves - same thing as in init, but this time updates it every wave
        # open the json file
        self.waveData = open('data\WaveData.json')
        self.contents = self.waveData.read()  # reads entire file into a single string
        # turns contents into a dictionary
        self.data = json.loads(self.contents)
        self.data = self.data["WaveData"]  # get list of dictionary
        # get wave name
        self.waveName = self.data[player.waveNumber - 1]["WaveName"]
        # get amount to kill
        self.toKill = self.data[player.waveNumber - 1]["EnemiesToKill"]
        # get which enemy types can spawn during this wave
        self.enemyTypesForWave = self.data[player.waveNumber - 1]["EnemyTypes"]
        # get the weights for each enemy type that can spawn during this wave
        self.enemyWeightsForWave = self.data[player.waveNumber -
                                             1]["EnemyTypesWeights"]
        self.waveData.close()

        # if not on final wave
        if not self.waveNumber == len(self.data):
            # if killed enough enemies
            if self.enemiesKilled >= self.toKill:
                # set the time when finished wave
                if not self.waveCompleted:
                    self.timeWaveDone = pygame.time.get_ticks()
                    self.waveCompleted = True
                # pause for a bit
                self.pauseTime = 1000
                # get the current time
                self.nowTime = pygame.time.get_ticks()
                if self.nowTime - self.timeWaveDone > self.pauseTime:
                    # reset stuff and increment wave counter
                    self.waveNumber += 1
                    self.enemiesSpawned = 0  # reset enemies spawned so more can spawn
                    self.enemiesKilled = 0
                    self.waveCompleted = False

    # call to take damage
    def takeDamage(self, healthToTake):
        self.currentHealth -= healthToTake
        # make player flash
        self.canFlash = True

    # respawn
    def respawn(self):
        # reset stuff
        self.currentHealth = self.maxHealth
        self.playerDead = False
        self.score = 0
        self.x = displayWidth / 2 - player.width / 2
        self.y = displayHeight / 2 - player.height / 2
        self.facingDirection = "right"
        self.canDrawDeathScreen = False
        self.timedDeath = False
        self.waveNumber = 1
        self.enemiesKilled = 0
        self.enemiesSpawned = 0


# bullet class
class Bullet:
    def __init__(self, x, y, facing):
        # bullet coordinates
        self.x = int(x)
        self.y = int(y)

        # self.bulletVelocity = pygame.math.Vector2(0, 0)

        # load player sprite
        self.bulletImg = pygame.image.load(
            'data\Sprites\Bullet.png').convert_alpha()

        # collision rect
        self.rect = pygame.Rect(self.x, self.y, 12, 12)

        # facing
        self.facing = facing

        # speed
        self.speed = 10

        # set speed depending on facing direction
        if facing == "left" or facing == "up" or facing == "left up" or facing == "left down":
            self.speed = -self.speed
        elif facing == "right" or facing == "down" or facing == "right up" or facing == "right down":
            self.speed = self.speed

    def drawBullet(self):
        gameDisplay.blit(self.bulletImg, (self.x, self.y))


# region Enemy Stuff
# enemy parent class
class Enemy:
    def __init__(self, x, y, w, h, movementSS, deathSS, speed, damage, health, scoreToGive):
        # enemy class
        self.x = int(x)
        self.y = int(y)

        # pixel dimensions
        self.width = w
        self.height = h

        # score to give
        self.scoreToGive = scoreToGive

        # offsets for death animation - make it centred
        self.offsetX = (120 - self.width) / 2
        self.offsetY = (120 - self.height) / 2

        # collision rect
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # load enemy sprites
        self.enemySS = sp.Spritesheet(movementSS)
        self.enemyImgs = []
        self.rectsAt = [(0, 0, w, h), (w, 0, w, h), (0, h, w, h), (w, h, w, h)]
        self.enemyImgs = self.enemySS.images_at(self.rectsAt, black)

        # sprite sheet for death
        self.deathSpritesheet = sp.Spritesheet(deathSS)
        self.deathImages = []
        self.rectsAt = [(0, 0, 120, 120), (120, 0, 120, 120), (240, 0, 120, 120), (0, 120, 120, 120), (
            120, 120, 120, 120), (240, 120, 120, 120), (0, 240, 120, 120), (120, 240, 120, 120), (240, 240, 120, 120)]
        # colour key (0,0,0) = black, removes black pixels
        self.deathImages = self.deathSpritesheet.images_at(
            self.rectsAt, black)

        self.currentImg = self.enemyImgs[0]

        # facing direction
        self.facingDirection = "right"

        # health stuff
        self.maxHealth = health
        self.health = self.maxHealth
        self.animCount = 0
        self.deathAnimFinished = False

        # enemy movement speed
        self.speed = speed

        # damage
        self.damage = damage

    # draw the enemy's sprite to the screen - move this to parent class
    def drawEnemy(self):
        # if at full health
        if not self.health <= 0 and self.health == self.maxHealth:
            # to show enemy hitbox = pygame.draw.rect(gameDisplay, white, self.rect)
            # change sprite depending on facing direction
            if self.facingDirection == "right":
                gameDisplay.blit(self.enemyImgs[0], (self.x, self.y))
                self.currentImg = self.enemyImgs[0]
            elif self.facingDirection == "left":
                gameDisplay.blit(self.enemyImgs[1], (self.x, self.y))
                self.currentImg = self.enemyImgs[1]
        # if lost a health - change to damaged state (only works on enemies with 2 health)
        elif not self.health <= 0 and self.health == self.maxHealth - 1:
            # change sprite depending on facing direction
            if self.facingDirection == "right":
                gameDisplay.blit(self.enemyImgs[2], (self.x, self.y))
                self.currentImg = self.enemyImgs[2]
            elif self.facingDirection == "left":
                gameDisplay.blit(self.enemyImgs[3], (self.x, self.y))
                self.currentImg = self.enemyImgs[3]
        # if dead
        elif self.health <= 0 and not self.deathAnimFinished:
            # death animation
            # we have 9 images for our death animation, and we show the same image for 3 frames
            # by using the number 27 as an upper bound for self.animCount because 27 / 3 = 9
            # 9 images shown 3 times each animation
            # whole divide animCount by 3 so each sprite is shown for 3 frames
            # subtracting the offset then centres it
            gameDisplay.blit(
                self.deathImages[self.animCount//3], (self.x - self.offsetX, self.y - self.offsetY))
            self.currentImg = self.deathImages[self.animCount//3]  # 3
            self.animCount += 1

            # if anim finishes, destory it
            if self.animCount + 1 >= 27:  # 27
                self.deathAnimFinished = True

    # follow player
    def followPlayer(self, player):
        # if not dead
        if not self.health <= 0:
            # difference in x
            difX = player.x - self.x
            # difference in y
            difY = player.y - self.y
            # distance between the 2 objects (pythagoras)
            distBetween = math.sqrt(difX ** 2 + difY ** 2)
            # normalise
            difX = difX / distBetween
            difY = difY / distBetween
            # change enemy's position
            self.x += difX * self.speed
            self.y += difY * self.speed

            # facing directions
            if player.x >= self.x:
                self.facingDirection = "right"
            elif player.x <= self.x:
                self.facingDirection = "left"

    # take damage
    def takeDamage(self, damageToTake, enemiesList):
        self.health -= damageToTake

        # if enemy health <= 0, kill it
        if self.health <= 0:
            # increment score and enemiesKilled by 1 for every enemy killed
            player.score += self.scoreToGive
            player.enemiesKilled += 1
            if self.deathAnimFinished:
                # destroy enemy object by removing it from enemies list
                enemiesList.pop(enemiesList.index(self))


# taco enemy class
class TacoEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 90, 50, 'data\Sprites\TacoEnemySS.png',
                         'data\Sprites\TacoDeathSS.png', 1.5, 1, 1, 1)

    def drawEnemy(self):
        return super().drawEnemy()

    def followPlayer(self, player):
        return super().followPlayer(player)

    def takeDamage(self, damageToTake, enemiesList):
        return super().takeDamage(damageToTake, enemiesList)


# burger enemy class
class BurgerEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 70, 65, 'data\Sprites\BurgerEnemySS.png',
                         'data\Sprites\BurgerDeathSS.png', 1.5, 2, 2, 2)
        # override
        self.offsetY = 30

    def drawEnemy(self):
        return super().drawEnemy()

    def followPlayer(self, player):
        return super().followPlayer(player)

    def takeDamage(self, damageToTake, enemiesList):
        return super().takeDamage(damageToTake, enemiesList)


# chips enemy class
class ChipsEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 70, 'data\Sprites\ChipsEnemySS.png',
                         'data\Sprites\ChipsDeathSS.png', 1.5, 1, 1, 2)
        # see if can move (for stopping)
        self.canMove = True
        self.canShoot = False
        self.setLastShoot = True
        self.shootCooldown = 2500
        self.lastShoot = pygame.time.get_ticks()

    def drawEnemy(self):
        return super().drawEnemy()

    def followPlayer(self, player):
        if not self.health <= 0:  # so it stops moving when dead
            # difference in x
            difX = player.x - self.x
            # difference in y
            difY = player.y - self.y
            # distance between the 2 objects (pythagoras)
            distBetween = math.sqrt(difX ** 2 + difY ** 2)
            # normalise
            difX = difX / distBetween
            difY = difY / distBetween

            # detect if enemy is actually on screen
            if self.x >= 75 and self.x <= displayWidth - 75 and self.y >= 75 and self.y <= displayHeight - 75:
                onScreen = True
            else:
                onScreen = False

            # so it stops moving once in range
            if distBetween <= 500 and onScreen:
                self.canMove = False
                self.canShoot = True
            elif self.canMove:
                # change enemy's position
                self.x += difX * self.speed
                self.y += difY * self.speed

            # shooting
            if self.canShoot:
                # spawn chip bullets every so often
                self.now = pygame.time.get_ticks()
                if self.now - self.lastShoot >= self.shootCooldown:
                    # spawn bullet at enemy centre
                    enemyBullets.append(EnemyBullet(self.x + self.width / 2,
                                                    self.y + self.height / 2, self))
                    # print(enemyBullets)
                    self.lastShoot = self.now

            # facing directions
            if player.x >= self.x:
                self.facingDirection = "right"
            elif player.x <= self.x:
                self.facingDirection = "left"

    def takeDamage(self, damageToTake, enemiesList):
        return super().takeDamage(damageToTake, enemiesList)


# enemy bullet class
class EnemyBullet:
    def __init__(self, x, y, parent):
        self.parent = parent

        # load bullet sprite
        self.bulletImg = pygame.image.load(
            'data\Sprites\Chip.png').convert_alpha()
        self.originalImg = self.bulletImg

        # collision rect
        self.rect = self.bulletImg.get_rect()

        # bullet coordinates
        self.x = int(x)
        self.y = int(y)

        # speed
        self.speed = 3.5

        # damage
        self.damage = 1

        # check to only get differences once
        self.hasGotDifs = False

        # set rotation relatives
        self.relX = (player.x + player.width / 2) - \
            (parent.x + parent.width / 2)
        self.relY = (player.y + player.height / 2) - \
            (parent.y + parent.height / 2)

    def drawBullet(self):
        # rotation
        self.angle = (180 / math.pi) * math.atan2(self.relX, self.relY)
        self.bulletImg = pygame.transform.rotate(
            self.originalImg, self.angle)
        self.rect = self.bulletImg.get_rect()

        gameDisplay.blit(self.bulletImg, (self.x, self.y))

    def moveInDirOfPlayer(self, player):
        # get difs once
        if not self.hasGotDifs:
            # go towards player centre
            # difference in x
            self.difX = (player.x + player.width / 2) - self.x
            # difference in y
            self.difY = (player.y + player.height / 2) - self.y
            self.hasGotDifs = True

        # distance between the 2 objects (pythagoras)
        self.distBetween = math.sqrt(self.difX ** 2 + self.difY ** 2)
        # normalise
        self.difX = self.difX / self.distBetween
        self.difY = self.difY / self.distBetween
        # change bullets's position
        self.x += self.difX * self.speed
        self.y += self.difY * self.speed


# spawn enemy
def spawnEnemyAtRanPos(enemyTypesList, enemyTypesWeightsList):
    # eval() executes a string as a command if it is valid
    # select a random enemy with respect to their weights (influence when spawning)
    ranEnemy = random.choices(enemyTypesList, enemyTypesWeightsList)
    xOrY = random.randint(0, 1)
    randomX = random.randint(0, displayWidth)
    randomY = random.randint(0, displayHeight)
    if xOrY == 0:  # x
        hOrL = random.randint(0, 1)  # on the upside or down side
        if hOrL == 0:  # up
            stringToEval = str(ranEnemy[0]) + \
                "(" + str(randomX) + ", " + str(-50) + ")"
            enemy = eval(stringToEval)
            enemies.append(enemy)
        elif hOrL == 1:  # down
            stringToEval = str(
                ranEnemy[0]) + "(" + str(randomX) + ", " + str(displayHeight + 50) + ")"
            enemy = eval(stringToEval)
            enemies.append(enemy)
    elif xOrY == 1:  # y
        lOrR = random.randint(0, 1)  # on the left side or right side
        if lOrR == 0:  # left
            stringToEval = str(ranEnemy[0]) + \
                "(" + str(-90) + ", " + str(randomY) + ")"
            enemy = eval(stringToEval)
            enemies.append(enemy)
        elif lOrR == 1:  # right
            stringToEval = str(
                ranEnemy[0]) + "(" + str(displayWidth + 90) + ", " + str(randomY) + ")"
            enemy = eval(stringToEval)
            enemies.append(enemy)
# endregion


# region UI
# text stuff
def textObjects(text, font, colour):
    textSurface = font.render(text, True, colour)
    return textSurface, textSurface.get_rect()


def messageDisplay(text, fontSize, textX, textY, colour):
    largeText = pygame.font.Font('data\pixelfont2.ttf', fontSize)
    textSurf, textRect = textObjects(text, largeText, colour)
    textRect.center = (textX, textY)
    gameDisplay.blit(textSurf, textRect)


# button stuff
def drawButton(display, width, height, x, y, buttonColourInactive, buttonColourActive, buttonText, fontSize, textColour, action=None):
    # if mouse in boundary
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    x = x - width / 2
    if x + width > mouse[0] > x and y + height > mouse[1] > y:
        pygame.draw.rect(display, buttonColourActive, (x, y, width, height))

        # button functionality
        if click[0] == 1 and action != None:
            action()
    else:
        pygame.draw.rect(display, buttonColourInactive, (x, y, width, height))
    # button text
    messageDisplay(buttonText, fontSize, x + width /
                   2, y + height / 2, textColour)


def drawTextOnlyButton(display, width, height, x, y, buttonColour, buttonText, fontSize, textColourInactive, textColourActive, action=None):
    # this button is for pressing a button that is just text with no box around it
    # if mouse in boundary
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    x = x - width / 2
    if x + width > mouse[0] > x and y + height > mouse[1] > y:
        pygame.draw.rect(display, buttonColour, (x, y, width, height))

        # button functionality
        if click[0] == 1 and action != None:
            action()

        messageDisplay(buttonText, fontSize, x + width /
                       2, y + height / 2, textColourActive)
    else:
        pygame.draw.rect(display, buttonColour, (x, y, width, height))
        # button text
        messageDisplay(buttonText, fontSize, x + width /
                       2, y + height / 2, textColourInactive)
# endregion


# quit game procedure
def quitGame():
    pygame.quit()
    quit()


# play game
def playGame():
    global canPlayGame
    canPlayGame = True
    player.respawn()


# quit to menu
def quitToMenu():
    global canPlayGame
    canPlayGame = False


# player initialisation
# subtracting half of length of the player centres it properly as (0, 0) = top left corner
player = Player(displayWidth / 2 - 30, displayHeight / 2 - 35)

# enemy initialisation
enemies = []

# bullets initialisation
bullets = []
enemyBullets = []


# what to redraw and update every frame
def updateFrame():
    # draw background
    gameDisplay.fill(greyBackground)

    # draw bullets
    for bullet in bullets:
        bullet.drawBullet()
        # move bullet rect (for collisions)
        bullet.rect = pygame.Rect(bullet.x, bullet.y, 12, 12)
    # enemy bullets
    for bullet in enemyBullets:
        bullet.drawBullet()
        bullet.moveInDirOfPlayer(player)
        # move bullet rect (for collisions)
        bullet.rect = pygame.Rect(bullet.x, bullet.y, 12, 12)

    # draw player
    player.drawPlayer()

    # draw enemies
    for enemy in enemies:
        enemy.drawEnemy()
        # move enemy rect (for collisions)
        if not enemy.health <= 0:  # if the enemy is not dead
            enemy.rect = pygame.Rect(
                enemy.x, enemy.y, enemy.width, enemy.height)
        # if enemy deaf
        elif enemy.health <= 0:
            # draw the rectangle as 0 width 0 height - it basically doesn't exist
            enemy.rect = pygame.Rect(enemy.x, enemy.y, 0, 0)

    # region UI
    if canPlayGame:
        if not player.playerDead:
            # score
            messageDisplay(str(player.score).zfill(
                7), 35, displayWidth - 87.5, 47.5, white)  # .zfill() pads with 0s
            # prints each heart with space between each other
            # heart backgrounds
            for i in range(0, player.maxHealth):
                gameDisplay.blit(heartImgs[1], (15 + i * 48 + i * 10, 15))
            # player's health
            for i in range(0, player.currentHealth):
                gameDisplay.blit(heartImgs[0], (15 + i * 48 + i * 10, 15))

            # waves stuff
            # check if enough waves in json file
            # if on final wave
            if player.waveNumber == len(player.data):
                messageDisplay(str(player.waveName), 30,
                               displayWidth / 2, 30, white)
                # progress bar
                # background
                pygame.draw.rect(gameDisplay, leafGreen,
                                 (displayWidth / 2 - 350, 50, 700, 15))
            # if not on final wave
            elif player.waveNumber - 1 < len(player.data):
                # get number of enemies that need to be killed
                percentKilled = (player.enemiesKilled / player.toKill) * 700
                # progress bar background
                pygame.draw.rect(gameDisplay, black,
                                 (displayWidth / 2 - 350, 50, 700, 15))
                # progress bar
                pygame.draw.rect(gameDisplay, leafGreen,
                                 (displayWidth / 2 - 350, 50, percentKilled, 15))
                # wave text
                if player.waveCompleted:
                    messageDisplay("Wave Completed!", 30,
                                   displayWidth / 2, 30, white)
                else:
                    messageDisplay(str(player.waveName), 30,
                                   displayWidth / 2, 30, white)
        # if player is dead draw the death screen ui
        else:
            # if havent drawn it yet, wait 1.25 seconds
            if not player.canDrawDeathScreen:
                drawDeathScreenCooldown = 1250
                nowDraw = pygame.time.get_ticks()
                if nowDraw - player.diedAt > drawDeathScreenCooldown:
                    player.canDrawDeathScreen = True
            else:
                # black game over box
                pygame.draw.rect(gameDisplay, black,
                                 (0, 0, displayWidth, displayHeight))

                # death text
                messageDisplay("You Died!", 220, displayWidth /
                               2, displayHeight / 2 - 20, appleRed)

                # score
                messageDisplay("Your score: " + str(player.score), 35, displayWidth /
                               2, displayHeight / 2 + 115, white)  # .zfill() pads with 0s
                # highscore
                f = open('data\highscore.txt', "r")
                highscore = f.readline()
                f.close()
                messageDisplay("Highscore: " + str(highscore), 35, displayWidth / 2,
                               displayHeight / 2 + 160, white)  # .zfill() pads with 0s

                # respawn
                drawTextOnlyButton(gameDisplay, 145, 30, displayWidth / 2, displayHeight /
                                   2 + 230, black, "Respawn", 35, leafGreen, lightLeafGreen, playGame)

                # quit
                drawTextOnlyButton(gameDisplay, 200, 26, displayWidth / 2, displayHeight /
                                   2 + 275, black, "Quit to Menu", 35, appleRed, lightAppleRed, quitToMenu)
    else:
        # menu stuff
        gameDisplay.blit(menuImg, (0, 0))
        # play game
        fontsize = 100
        drawTextOnlyButton(gameDisplay, (2.25 * fontsize), (0.9 * fontsize), displayWidth / 2, displayHeight /
                           2, greyBackground, "Play", fontsize, leafGreen, lightLeafGreen, playGame)
        drawTextOnlyButton(gameDisplay, (2 * fontsize), (0.8 * fontsize), displayWidth / 2, displayHeight /
                           2 + 300 / 2, greyBackground, "Quit", fontsize, appleRed, lightAppleRed, quitGame)
    # endregion

    # update
    player.update()
    pygame.display.update()


# main game loop
def gameLoop():
    gameRunning = True

    # global variables used
    global lastFire
    global lastSpawn
    global lastHit

    # game loop
    while gameRunning:

        # set the framefrate
        clock.tick(120)

        # updates variables if window size changes
        displayWidth = pygame.display.get_surface().get_width()
        displayHeight = pygame.display.get_surface().get_height()

        # events
        #################################
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gameRunning = False
        #################################

            # if player dead = cant move
            if not player.playerDead and canPlayGame:
                # player movement on key down and player stop on key up
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        player.leftPressed = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        player.rightPressed = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        player.upPressed = True
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        player.downPressed = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        player.leftPressed = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        player.rightPressed = False
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        player.upPressed = False
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        player.downPressed = False

        # if not in menu
        if canPlayGame:
            # if player is dead - stop all these things
            if not player.playerDead:
                # move or destory bullets
                for bullet in bullets:
                    # only move if within screen
                    if bullet.x < displayWidth and bullet.x > 0 and bullet.y < displayHeight and bullet.y > 0:
                        if "left" in bullet.facing or "right" in bullet.facing:
                            bullet.x += bullet.speed
                        elif bullet.facing == "up" or bullet.facing == "down":
                            bullet.y += bullet.speed
                    else:
                        # remove bullet
                        bullets.pop(bullets.index(bullet))

                # enemy bullet collision with screen
                for bullet in enemyBullets:
                    # only move if within screen
                    if not (bullet.x < displayWidth and bullet.x > 0 and bullet.y < displayHeight and bullet.y > 0):
                        # remove bullet
                        enemyBullets.pop(enemyBullets.index(bullet))

                # move enemies
                for enemy in enemies:
                    enemy.followPlayer(player)

                # shooting and cooldown
                shootCooldown = 500  # 0.5 second cooldown
                keys = pygame.key.get_pressed()

                if keys[pygame.K_SPACE]:
                    # shoot if press space
                    now = pygame.time.get_ticks()
                    if now - lastFire >= shootCooldown:
                        bullets.append(Bullet(player.x + player.width / 2,
                                              player.y + player.height / 2, player.facingDirection))
                        lastFire = now

                # spawn enemies
                # during wave mode - limited spawns
                if player.waveNumber < len(player.data):
                    enemiesToSpawn = player.data[player.waveNumber -
                                                 1]["EnemiesToKill"]
                    if player.enemiesSpawned < enemiesToSpawn:
                        now = pygame.time.get_ticks()
                        if now - lastSpawn >= spawnCooldown:
                            spawnEnemyAtRanPos(
                                player.enemyTypesForWave, player.enemyWeightsForWave)
                            lastSpawn = now
                            player.enemiesSpawned += 1
                # endless mode - endless spawns
                else:
                    now = pygame.time.get_ticks()
                    if now - lastSpawn >= spawnCooldown:
                        spawnEnemyAtRanPos(
                            player.enemyTypesForWave, player.enemyWeightsForWave)
                        lastSpawn = now
                        player.enemiesSpawned += 1

                # player collisions with the wall
                if player.x > displayWidth - player.width:
                    player.hasCollidedRight = True
                elif player.x < 0:
                    player.hasCollidedLeft = True
                else:
                    player.hasCollidedRight = False
                    player.hasCollidedLeft = False

                if player.y > displayHeight - player.height:
                    player.hasCollidedDown = True
                elif player.y < 0:
                    player.hasCollidedUp = True
                else:
                    player.hasCollidedUp = False
                    player.hasCollidedDown = False

                # collisions between bullet and enemies
                for bullet in bullets:
                    for enemy in enemies:
                        # check if they have collided, if enemy is dead, don't collide
                        if bullet.rect.colliderect(enemy.rect) and not enemy.health <= 0:
                            # remove bullet from bullet list
                            if bullet in bullets:
                                bullets.pop(bullets.index(bullet))
                            # make enemy take damage
                            enemy.takeDamage(1, enemies)

                # collisions between player and enemies
                now = pygame.time.get_ticks()
                for enemy in enemies:
                    if enemy.rect.colliderect(player.rect):
                        if now - lastHit >= player.hitCooldown:   # invulnerability cooldown
                            player.takeDamage(enemy.damage)
                            lastHit = now

                # collisions between player and enemy bullets
                for bullet in enemyBullets:
                    if bullet.rect.colliderect(player.rect):
                        if now - lastHit >= player.hitCooldown:   # invulnerability cooldown
                            player.takeDamage(bullet.damage)
                            # destroy bullet
                            enemyBullets.pop(enemyBullets.index(bullet))
                            lastHit = now

                # player flash
                nowCount = pygame.time.get_ticks()
                # is hitcooldown is over - basically the player can only flash after the player has been hit and before the hitcooldown resets
                if now - lastHit < player.hitCooldown - 150:
                    if nowCount - player.lastFlash >= player.flashCooldown:  # cooldown of every flash
                        player.shouldFlash = not player.shouldFlash
                        player.lastFlash = nowCount
                else:
                    player.canFlash = False

            # if player is dead
            if player.playerDead:
                # set to not transparent
                player.currentImg.set_alpha(255)
                # kill all enemies
                if len(enemies) > 0:
                    for enemy in enemies:
                        # set enemy health to 0
                        enemy.health = 0
                        if enemy.deathAnimFinished:
                            # destroy enemy object
                            enemies.pop(enemies.index(enemy))
                # remove all bullets
                if len(bullets) > 0:
                    for bullet in bullets:
                        bullets.pop(bullets.index(bullet))
                if len(enemyBullets) > 0:
                    for bullet in enemyBullets:
                        enemyBullets.pop(enemyBullets.index(bullet))
                # reset player's velocity and 'pressed' bools
                player.playerVelocity[0] = 0
                player.playerVelocity[1] = 0
                player.leftPressed = False
                player.rightPressed = False
                player.upPressed = False
                player.downPressed = False

                # log highcore
                f = open('data\highscore.txt', "r")
                scoreToCheck = f.readline()
                f.close()
                if player.score > int(scoreToCheck):
                    f = open('data\highscore.txt', "w")
                    f.write(str(player.score))
                    f.close()

        updateFrame()


gameLoop()
# quitGame()
