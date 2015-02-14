import os, pygame, time, picamera, pgmagick, io, sys
from pygame.locals import *

FPS = 25


#               R    G    B    A
WHITE       = (255, 255, 255, 255)
GRAY        = (185, 185, 185, 255)
BLACK       = (  0,   0,   0, 255)
DARKBLUE    = (  0,   0, 100, 255)
TEXTSHADOWCOLOR = GRAY
TEXTCOLOR = WHITE
BGCOLOR = DARKBLUE

# layout - each "grid" is 8x8px at 640x480
grid_width = 80
grid_height = 60

# photo preview in grid units
preview_pad    = 1
preview_x      = 4
preview_y      = 14
preview_width  = 48
preview_height = 40

# thumb strip in grid units
thumb_strip_pad    = 1
thumb_strip_x      = 54
thumb_strip_y      = 0
thumb_strip_width  = 20
thumb_strip_height = grid_height
thumb_photo_width  = thumb_strip_width - 2 * thumb_strip_pad
thumb_photo_height = thumb_photo_width * 3 / 4

# font sizes in grid units
basic_font_size    = 4
big_font_size      = 8
huge_font_size     = 50

thumb_size = (400,300)
thumb_time = 2
thumb_last_sw = 0
thumb_index = 1
thumb_loc = '/usr/photobooth/photos_thumb/'
thumb_strip = []

preview_resolution = (400,300)
preview_alpha  = 200
blank_thumb = (20,20,20,255)

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT, HUGEFONT, WINDOWWIDTH, WINDOWHEIGHT, CAMERA, GRID_W_PX, GRID_H_PX
    setupDisplay()
    pygame.init()
    WINDOWWIDTH = pygame.display.Info().current_w
    GRID_W_PX   = WINDOWWIDTH / grid_width
    WINDOWHEIGHT = pygame.display.Info().current_h
    GRID_H_PX    = WINDOWHEIGHT / grid_height
    FPSCLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False) #hide the mouse cursor
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), pygame.FULLSCREEN, 32)
    BASICFONT = pygame.font.Font('freesansbold.ttf', int(GRID_H_PX * basic_font_size))
    BIGFONT = pygame.font.Font('freesansbold.ttf', int(GRID_H_PX * big_font_size))
    HUGEFONT = pygame.font.Font('freesansbold.ttf', int(GRID_H_PX * huge_font_size))
    pygame.display.set_caption('Photobooth')
    
    CAMERA = picamera.PiCamera()
    
    showTextScreen('Photobooth','Loading...')

    loadThumbs()
    while True:
        #checkForQuit()
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate() # terminate if the KEYDOWN event was for the Esc key
                elif event.key == K_SPACE:
                    DISPLAYSURF.fill(WHITE)
                    pygame.display.update()
                    print 'Take Photos'
                    photoShoot(4)
        idleScreen()
    
    terminate()
    
def photoShoot(numPhotos):
    image = []
    DISPLAYSURF.fill(BLACK)
    CAMERA.preview_fullscreen = True
    CAMERA.preview_alpha = preview_alpha
    readySurf, readyRect = makeTextObjs('Get Ready', BIGFONT, WHITE)
    readyRect.midbottom = (WINDOWWIDTH/2,WINDOWHEIGHT/10*9)
    DISPLAYSURF.blit(readySurf, readyRect)
    pygame.display.update()
    time.sleep(1)
    
    for photo in range (0,numPhotos):
        time.sleep(0.1)
        for i in range (3,0,-1):
            DISPLAYSURF.fill(BLACK)
            numSurf, numRect = makeTextObjs(str(i), HUGEFONT, WHITE)
            numRect.center = (WINDOWWIDTH/2,WINDOWHEIGHT/2- GRID_H_PX)
            DISPLAYSURF.blit(numSurf, numRect)
            numphotosSurf, numphotosRect = makeTextObjs('Taking Photo ' + str(photo+1) + ' of ' + str(numPhotos),BIGFONT,WHITE)
            numphotosRect.midbottom = (WINDOWWIDTH / 2, WINDOWHEIGHT - GRID_H_PX * 4)
            DISPLAYSURF.blit(numphotosSurf, numphotosRect)
            pygame.display.update()
            time.sleep(0.7)
        DISPLAYSURF.fill(BLACK)
        pygame.display.update()
        #showTextScreen('Taking Photo ' + str(photo+1),'Taking ' + str(numPhotos) + ' Photos Total')
        image.append(takePhoto())
    DISPLAYSURF.fill(BLACK)
    pygame.display.update()
    CAMERA.stop_preview()
    showTextScreen('Photobooth','Processing...')
    for rawimage in image:
        processPhoto(rawimage)
        updateThumb(rawimage)
    
    CAMERA.resolution = preview_resolution
    CAMERA.preview_fullscreen = False
    CAMERA.start_preview()
    
def processPhoto(photo):
    photo_edit = pgmagick.Image(photo)
    photo_edit.quality(100)
    photo_edit.scale(str(thumb_size[0])+'x'+str(thumb_size[1]))
    photo_edit.write(thumb_loc+'1.jpg')
    #updateThumb(thumb_loc+'1.jpg')
    print 'photo processed'
    
def takePhoto():
    CAMERA.stop_preview()
    CAMERA.resolution = (2592,1944)
    tmp_name = int(time.time())
    tmp_name = '/usr/photobooth/raw_images/' + str(tmp_name) + '.jpg'
    CAMERA.led = True
    CAMERA.capture(tmp_name,'jpeg',False, None, None,quality=100)
    CAMERA.led = False
    CAMERA.resolution = preview_resolution
    CAMERA.preview_fullscreen = True
    CAMERA.start_preview()
    
    return tmp_name

def idleScreen():
    global thumb_last_sw
    CAMERA.preview_fullscreen = False
    CAMERA.resolution = preview_resolution
    CAMERA.preview_window = (GRID_W_PX * (preview_x + preview_pad),GRID_H_PX * (preview_y + preview_pad),GRID_W_PX * (preview_width - (2 * preview_pad)),GRID_H_PX * (preview_height - (2 * preview_pad)))
    CAMERA.preview_alpha = preview_alpha
    CAMERA.led = False
    DISPLAYSURF.fill(BGCOLOR)
    border = pygame.Surface((GRID_W_PX * preview_width, GRID_H_PX * preview_height))
    border.fill(BLACK)
    borderRect = DISPLAYSURF.blit(border,(GRID_W_PX * preview_x, GRID_H_PX * preview_y))
    startSurf, startRect = makeTextObjs('Press Start', BASICFONT, WHITE)
    startRect.midbottom = (borderRect[2]/2+borderRect[0],borderRect[3]+borderRect[1]-10)
    DISPLAYSURF.blit(startSurf, startRect)
    titleSurf, titleRect = makeTextObjs('Photobooth', BIGFONT, GRAY)
    titleRect.bottomleft = (borderRect[0] + preview_pad * GRID_W_PX ,borderRect[1])
    DISPLAYSURF.blit(titleSurf, titleRect)
    CAMERA.start_preview()
    pygame.display.update()
    thumb_last_sw = 0
    while not pygame.event.peek(KEYDOWN):
        pygame.display.update(filmStrip())
        FPSCLOCK.tick(FPS)

def filmStrip():
    global thumb_index, thumb_last_sw
    if time.time() - thumb_time> thumb_last_sw:
        thumb_last_sw = time.time()
        strip = pygame.Surface((thumb_strip_width * GRID_W_PX, thumb_strip_height * GRID_H_PX),pygame.SRCALPHA)
        strip.fill(BLACK)
        thumb_h_pos = (thumb_photo_height + thumb_strip_pad) * GRID_H_PX
        thumb_index += 1
        for i in range (0,8):
            strip.blit(thumb_strip[i],(thumb_strip_pad * GRID_W_PX,((thumb_index+i)%8)*thumb_h_pos))
        return DISPLAYSURF.blit(strip,(GRID_W_PX * thumb_strip_x, GRID_H_PX * thumb_strip_y))

def updateThumb(image):
    global thumb_strip
    thumb_size = (int(thumb_photo_width * GRID_W_PX), int(thumb_photo_height * GRID_H_PX))
    for i in range (7,0,-1):
        try:
            thumb_strip[i] = thumb_strip[i - 1]
        except:
            thumb_strip[i] = pygame.Surface(thumb_size)
            thumb_strip[i].fill(blank_thumb)
        #try:
        os.rename(thumb_loc+str(i)+'.jpg',thumb_loc+str(i+1)+'.jpg')
        #except:
        #    continue
    photo_edit = pgmagick.Image(image)
    photo_edit.quality(100)
    photo_edit.scale(str(thumb_size[0])+'x'+str(thumb_size[1]))
    photo_edit.write(thumb_loc+'1.jpg')
    thumb_strip[0] = pygame.image.load(image).convert()
    thumb_strip[0] = pygame.transform.smoothscale(thumb_strip[0],thumb_size)
        
def loadThumbs():
    global thumb_strip
    thumb_size = (int(thumb_photo_width * GRID_W_PX), int(thumb_photo_height * GRID_H_PX))
    for i in range (0,8):
        try:
            thumb_strip.append(pygame.image.load(thumb_loc+str(i+1)+'.jpg').convert())
            thumb_strip[i] = pygame.transform.smoothscale(thumb_strip[i],thumb_size)
        except:
            thumb_strip.append(pygame.Surface(thumb_size))
            thumb_strip[i].fill(blank_thumb)

def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def terminate():
    CAMERA.stop_preview()
    CAMERA.close()
    pygame.quit()
    sys.exit()

def checkForQuit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    for event in pygame.event.get(KEYUP): # get all the KEYUP events
        if event.key == K_ESCAPE:
            terminate() # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event) # put the other KEYUP event objects back

def showTextScreen(text, text2):
    # This function displays large text in the
    
    # Draw the text drop shadow
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTSHADOWCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the text
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the additional "Press a key to play." text.
    pressKeySurf, pressKeyRect = makeTextObjs(text2, BASICFONT, TEXTCOLOR)
    pressKeyRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    pygame.display.update()

def setupDisplay():
    disp_no = os.getenv("DISPLAY")
    if disp_no:
        print "I'm running under X display = {0}".format(disp_no)
    
    # Check which frame buffer drivers are available
    # Start with fbcon since directfb hangs with composite output
    drivers = ['fbcon', 'directfb', 'svgalib']
    found = False
    for driver in drivers:
        # Make sure that SDL_VIDEODRIVER is set
        if not os.getenv('SDL_VIDEODRIVER'):
            os.putenv('SDL_VIDEODRIVER', driver)
        try:
            pygame.display.init()
        except pygame.error:
            print 'Driver: {0} failed.'.format(driver)
            continue
        found = True
        break

    if not found:
        raise Exception('No suitable video driver found!')

if __name__ == '__main__':
    main()
