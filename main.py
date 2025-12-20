import pygame, keyboard, random, dataclasses, threading
pygame.font.init()
pygame.init()

pygame.display.set_caption('Ectonomy Release')
pygame.display.set_icon(pygame.image.load('textures/icon.ico'))

class textures:
    bath = pygame.image.load('textures/bath.png')
    bed = pygame.image.load('textures/bed.png')
    door_open = pygame.image.load('textures/door_open.png')
    door = pygame.image.load('textures/door.png')
    footwash = pygame.image.load('textures/footwash.png')
    granny = pygame.image.load('textures/granny.png')
    lift_open = pygame.image.load('textures/lift_open.png')
    lift = pygame.image.load('textures/lift.png')
    notebook = pygame.image.load('textures/notebook.png')
    open_notebook = pygame.image.load('textures/open_notebook.png')
    open_pipe = pygame.image.load('textures/open_pipe.png')
    pipe = pygame.image.load('textures/pipe.png')
    open_window = pygame.image.load('textures/open_window.png')
    window = pygame.image.load('textures/window.png')
    phone = pygame.image.load('textures/phone.png')
    scoreboard = pygame.image.load('textures/scoreboard.png')
    shell = pygame.image.load('textures/shell.png')
    wasted = pygame.image.load('textures/wasted.png')
    player = pygame.image.load('textures/player.png')

screen_size = (32*26, 32*18)
screen = pygame.display.set_mode(screen_size) #, pygame.FULLSCREEN | pygame.SCALED
screen.set_alpha(0)
fps = 60
delta_time = 1 / fps
clock = pygame.time.Clock()
target_scene = None
total_time = 120
total_speed = 7
total_cost = 0.05
telled = False
gamerun = True

class difficults:
    easy = (120, 7, 0.05)
    normal = (135, 6, 0.08)
    hard = (150, 4, 0.13)

difficult = 1
difficult_list = [difficults.easy, difficults.normal, difficults.hard]

def setTargetScene(scene):
    global target_scene
    target_scene = scene

def getTargetScene():
    global target_scene
    return target_scene

ttcd = 0.3
def setDifficult():
    global total_cost, total_speed, total_time, difficult, ttcd

    ttcd -= delta_time
    if ttcd > 0: return 0
    ttcd = 0.3

    difficult += 1 if difficult < 3 else -2
    total_time, total_speed, total_cost = difficult_list[difficult-1]


@dataclasses.dataclass
class Object:

    x : int
    y : int
    width : int
    height : int
    color : tuple = (255, 255, 255)
    hitbox = pygame.Rect(0,0,0,0)
    texture : pygame.surface.Surface = textures.window

    def __call__(self, screen, scene, *args, **kwds):
        self._Hitbox(scene)
        self._Draw(screen)

    def _Hitbox(self, scene):
        self.hitbox = pygame.Rect(
            self.x+scene.position[0],
            self.y+scene.position[1],
            self.width,
            self.height
        )
    
    def _Draw(self, screen):
        if self.texture is None:
            pygame.draw.rect(
                screen, self.color, self.hitbox
            )
        else:
            _texture = pygame.transform.scale(self.texture, (self.width, self.height))
            screen.blit(_texture, (self.hitbox.x, self.hitbox.y))

class Scoreboard(Object):

    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        super().__init__(
            x, y, width, height, color, texture=textures.scoreboard
        )
    
    def Open(self, screen, manager, flags_group, timer, player):
        global gamerun
        while gamerun:

            screen.fill((0,0,0))
            clock.tick(fps)

            for event in pygame.event.get():
                if event.type == pygame.quit:
                    pass

            manager(flags_group)
            if timer.timer <= 0 and timer.timer != -1:
                EndCostScreen(player, manager)
            if timer.timer >= 0: timer.timer -= delta_time
            if keyboard.is_pressed('esc'): break

            screen.blit(pygame.transform.scale(textures.scoreboard, [screen_size[0]/2,screen_size[1]/2]), ([screen_size[0]/4,screen_size[1]/4]))

            _font = pygame.font.Font(None, 100)
            _surf = _font.render(
                str(manager.cost)[0:3+len(str(manager.cost).split('.')[0])],
                False,
                (255, 255, 255)
            )
            screen.blit(
                _surf,
                (
                    290,
                    190
                )
            )

            pygame.display.flip()

    def __call__(self, screen, scene, player, manager, timer, flags_group, *args, **kwds):
        super().__call__(
            screen, scene, *args, **kwds
        )
        mx, my = pygame.mouse.get_pos()
        prs, _, _ = pygame.mouse.get_pressed()
        if self.hitbox.collidepoint(mx, my) and player.action_hitbox.colliderect(self.hitbox) and prs:
            return self.Open(screen, manager, flags_group, timer, player)

class FlagObject(Object):

    def __init__(self, x, y, width, height, color=(255, 255, 255), texture=textures.scoreboard, texture_true=textures.door): #scoreboard - неакитвный, door - активный
        super().__init__(
            x, y, width, height, color, texture=texture
        )
        self.const_texture = texture #
        self.const_texture_true = texture_true #
        self.const_color = color
        self.flag = False

    def __call__(self, screen, scene, player, *args, **kwds):
        super().__call__(screen, scene, *args, **kwds)
        self.color = (0, 255, 0) if self.flag else (255, 255, 255)
        self.texture = self.const_texture_true if self.flag else self.const_texture #
        mx, my = pygame.mouse.get_pos()
        prs, _, _ = pygame.mouse.get_pressed()
        if self.hitbox.collidepoint(mx, my) and player.action_hitbox.colliderect(self.hitbox) and prs and self.flag:
            self.flag = not self.flag

class Door(Object):

    def __init__(self, x, y, width, height, scene, color=(255, 255, 255), canOpen=True, texture=textures.door, texture_true=textures.door_open):
        super().__init__(
            x, y, width, height, color, texture=texture
        )
        self.const_texture = texture #
        self.const_texture_true = texture_true #
        self.target_scene = scene
        self.canOpen = canOpen

    def __call__(self, screen, scene, player, *args, **kwds):
        super().__call__(
            screen, scene, *args, **kwds
        )
        self.color = (0, 100, 0) if player.hitbox.colliderect(self.hitbox) else (0, 30, 0)
        self.texture = self.const_texture_true if player.hitbox.colliderect(self.hitbox) else self.const_texture #
        if player.hitbox.colliderect(self.hitbox) and keyboard.is_pressed('e') and self.canOpen and player.door_open_cooldown <= 0:
            player.door_open_cooldown = 1
            setTargetScene(self.target_scene)

class Wasted(FlagObject):
    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        super().__init__(
            x, y, width, height, color
        )
        self.const_texture = textures.wasted
        self.const_texture_true = textures.wasted
        self.texture = textures.wasted
        self.flag = True
        self.collected = False

    def __call__(self, screen, scene, player, *args, **kwds):
        if not self.flag:
            if player.inventory < 3:
                player.inventory += 1
                self.collected = True
                self.flag = True
            else:
                self.flag = True

        if not self.collected: 
            super().__call__(
                screen, scene, player, *args, **kwds
            )

class Replic:
    
    def __init__(self, repl, speed=4):
        self.replics = repl
        self.continued = 0
        self.cooldown = speed
        self.const_cooldown = self.cooldown
        self.finished = False

    def Render(self, screen):
        if self.continued == len(self.replics):
            self.finished = True

        if self.finished:
            return 0
        
        font = pygame.font.Font(None, 40)
        _text = self.replics[self.continued][0:round(((self.const_cooldown-self.cooldown)*len(self.replics[self.continued]))/self.const_cooldown+1)]
        _surf = font.render(
            _text,
            False,
            (0, 0, 0),
            (255, 255, 255)
        )

        self.cooldown -= delta_time

        screen.blit(
            _surf,
            (
                (screen_size[0]-_surf.get_width())/2,
                screen_size[1]-_surf.get_height()-60
            )
        )

        if self.cooldown <= -0.5:
            
            if self.continued < len(self.replics):
                self.continued += 1
            
            self.cooldown = self.const_cooldown

class Npc(FlagObject):

    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        super().__init__(x, y, width, height, color)
        self.flag = True
        self.dialogued = False
        self.dialog = Replic(['Привет внучек! Не мог бы ты сделать услугу?', 'Можешь убрать подъезд от мусора, а я заплачу.', 'Деньгами не обижу.'])
        self.texture = textures.granny
        self.const_texture = textures.granny
        self.const_texture_true = textures.granny

    def __call__(self, screen, scene, player, *args, **kwds):
        if not self.flag and not self.dialogued:
            self.dialogued = True

        elif not self.flag and self.dialogued == 'v':
            player.balance += player.inventory*3
            player.inventory = 0
            self.flag = not self.flag
        
        if self.dialogued:
            self.dialog.Render(screen)
        
        if self.dialog.finished:
            self.dialogued = 'v'

        return super().__call__(screen, scene, player, *args, **kwds)

class Phone(FlagObject):

    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        super().__init__(x, y, width, height, color)
        self.flag = True
        self.dialogued = False
        self.st = False
        self.const_texture_true = textures.phone
        self.const_texture = textures.phone
        self.texture = textures.phone
        self.dialog = Replic(['Добрый день! Пришло время платить коммуналку.', 'Через 2 минуты вам придет счёт.', 'Его нужно оплатить сразу.'])

    def _Draw(self, screen):
        if getTargetScene().id == 0: super()._Draw(screen)

    def __call__(self, screen, scene, player, manager, timer, *args, **kwds):
        global telled

        if not self.flag and self.dialogued == False:
            self.dialogued = True
        
        if self.dialogued == True:
            self.dialog.Render(screen)
        
        if self.dialog.finished:
            self.dialogued = 'v'
            self.st = True
            
        if self.st == True and timer.timer == -1:
            timer.timer = total_time
            telled = True
        
        return super().__call__(screen, scene, player, *args, **kwds)

class Player(Object):

    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        super().__init__(
            x, y, width, height, color
        )
        #self.action_hitbox = pygame.Rect(0,0,0,0)
        self.action_hitbox = None
        self.speed = 3
        self.inventory = 0
        self.balance = 0

        self.door_open_cooldown = 0

        self.texture = textures.player

        self.fading = 'right'
        self.old_fading = 'right'
    
    def _Hitbox(self, scene):
        radius = 50

        self.action_hitbox = pygame.Rect(
            self.x+scene.position[0]-radius,
            self.y+scene.position[1]-radius,
            self.width+2*radius,
            self.height+2*radius
        )

        return super()._Hitbox(scene)
    
    def _Draw(self, screen):
        _texture = pygame.transform.scale(self.texture, (self.width, self.height))
        screen.blit(_texture, (self.hitbox.x, self.hitbox.y))
        #pygame.draw.rect(screen, (0, 255, 0), self.hitbox)
    
    def Text(self, screen):
        _font = pygame.font.Font(None, 46)

        _surf = _font.render(
            str(self.balance)+'$',
            False, (255, 255, 255),
            (0, 0, 0)
        )
        if self.balance > 0:
            screen.blit(_surf, (10, 10))

        _surf = _font.render(
            str(self.inventory)+'/3 мусора',
            False,
            (255, 255, 255),
            (0, 0, 0)
        )

        if self.inventory > 0:
            screen.blit(_surf, (10, 50))

    def __call__(self, screen, scene, *args, **kwds):
        #pygame.draw.rect(screen, (0, 255, 0), self.action_hitbox)
        self.door_open_cooldown -= delta_time
        self.Text(screen)

        super().__call__(
            screen, scene, *args, **kwds
        )

        if keyboard.is_pressed('a') and self.x > 0:
            self.x -= self.speed * self.width * delta_time
            self.fading = 'left'

        elif keyboard.is_pressed('d') and self.x + self.width < scene.size[0]:
            self.x += self.speed * self.width * delta_time
            self.fading = 'right'
        
        if self.old_fading != self.fading: self.texture = pygame.transform.flip(self.texture, flip_x=1, flip_y=0)
        self.old_fading = self.fading

class Scene:

    def __init__(self, size, pos, id, fixed=False):
        self.id = id
        self.collection = []
        self.size  = size
        self.position = pos if type(pos) == tuple else ((pos[0]-self.size[0])/2, (pos[1]-self.size[1])/2)
        self.fixed = fixed

    def addObject(self, object : Object):
        self.collection.append(object)

@dataclasses.dataclass
class Manager:

    cost : int = 0.0
    timeout : int = total_speed
    const_timeout : int = timeout
    
    def __call__(self, flags_group, *args, **kwds):
        if not telled:
            return 0

        self.timeout -= delta_time

        k = len(
            [ el for el in flags_group if el[1].flag ]
        )
        self.cost += (total_cost*k)*delta_time

        if self.timeout <= 0:

            if len(flags_group) == 0:
                return 0
            
            random_index = random.randint(0, len(flags_group)-1)
            if not flags_group[random_index][1].flag:
                flags_group[random_index][1].flag = True
                self.timeout = self.const_timeout

@dataclasses.dataclass
class Timer:
    def __init__(self): self.timer = -1

class Button:

    def __init__(self, x, y, sz, text):
        self.x, self.y = x, y
        self.text = text
        self.sz = sz
    
    def __call__(self, screen, action = lambda _: 0, color=(255, 255, 255), *args, **kwds):
        _font = pygame.font.Font(None, self.sz)
        _color = color
        __color = (100, 100, 100)
        _surf = _font.render(
            self.text,
            False, _color,
            (0, 0, 0)
        )

        hitbox = pygame.Rect(self.x, self.y, _surf.get_width(), _surf.get_height())
        if hitbox.collidepoint(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]):
            __color = (120, 120, 120)
            if pygame.mouse.get_pressed()[0]:
                action(None)
        
        
        _surf = _font.render(
            self.text,
            False, _color,
            __color
        )   

        screen.blit(_surf, (self.x, self.y))

def Menu():

    def endg():
        global gamerun
        gamerun = False

    nullScene = Scene((32*20, 32*9), list(screen_size), id=993)
    
    entrance_room_menu = Scene((32*20, 32*9), list(screen_size), id=-2)
    entrance_room_menu.addObject(Door(20, entrance_room_menu.size[1]-150, 100, 150, canOpen=False, scene=None))
    entrance_room_menu.addObject(Door(140, entrance_room_menu.size[1]-150, 100, 150, canOpen=False, scene=None))
    entrance_room_menu.addObject(Door(300, entrance_room_menu.size[1]-170, 180, 170, canOpen=False, scene=None, texture=textures.lift, texture_true=textures.lift_open))
    entrance_room_menu.addObject(Object(500, entrance_room_menu.size[1]-140, 100, 140, texture=textures.granny))
    
    for i in range(random.randint(3, 5)):
        entrance_room_menu.addObject(Object(random.randint(0, entrance_room_menu.size[0]-40), entrance_room_menu.size[1]-40, 40, 40, color=(0, 255, 0), texture=textures.wasted))
    
    setTargetScene(entrance_room_menu)

    global gamerun
    while gamerun:
        screen.fill((0, 0, 0))
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gamerun = False
        
        _font = pygame.font.Font(None, 30)
        _color = (30, 30, 30)
        _surf = _font.render(
            'Developer: Lixpan4ik',
            False, _color,
            (0, 0, 0)
        )
        screen.blit(_surf, (0, screen_size[1]-_surf.get_height()))

        pygame.draw.rect(
            screen,
            (
                20, 20, 20
            ),
            pygame.Rect(
                getTargetScene().position[0], 
                getTargetScene().position[1],
                getTargetScene().size[0],
                getTargetScene().size[1]
            )
        )

        for obj in getTargetScene().collection:
            obj(
                screen, getTargetScene(), Player(1,1,1,1), Manager(1,1,1), Timer()
            )

        _font = pygame.font.Font(None, 100)
        _color = (255, 255, 255)
        _surf = _font.render(
            'Ectonomy',
            False, _color,
            (10, 10, 10)
        )
        screen.blit(_surf, (50, 100))

        Button(50, 200, 60, 'Play')(screen, lambda _: Main())

        _color = ()
        if difficult == 1: _color = (0, 200, 0)
        elif difficult == 2: _color = (200, 200, 0)
        elif difficult == 3: _color = (200, 0, 0)
        Button(50, 250, 60, 'Difficult')(screen, lambda _: setDifficult(), color=_color)
        Button(50, 300, 60, 'Education')(screen, lambda _: Education())
        Button(50, 350, 60, 'Quit')(screen, lambda _: endg())

        pygame.display.flip()

def Education():
    educ = Replic([
        'Ответив на звонок, запускаетсяя таймер.',
        'В доме начинают открываться объекты.',
        'Включенные и открытые объекты поглащают энергию.',
        'Этим они крутят счетчик.',
        'Через время таймера, придут коллеторы.',
        'Они возьмут ваши деньги.',
        'Если денег не хватит, вы будете избиты.',
        'Деньги можно получить, сдав мусор бабусе.',
        'Но нельзя забывать про счетчик.',
        '...'
    ], speed=2)
    tiles = [
        textures.phone,
        textures.window,
        textures.open_notebook,
        textures.scoreboard,
        None,
        None,
        None,
        textures.granny,
        textures.wasted,
        None
    ]

    global gamerun
    while gamerun:

        if keyboard.is_pressed('p'):
            Menu()

        screen.fill((0, 0, 0))
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gamerun = False
        
        try: screen.blit(pygame.transform.scale(tiles[educ.continued], (200, 200)), ((screen_size[0]-200)/2, (screen_size[1]-200)/2))
        except: pass

        educ.Render(screen)
        if educ.finished:
            Menu()
        
        pygame.display.flip()

def EndCostScreen(player : Player, manager : Manager):
    titres = Replic(['Спасибо за прохождение', 'Игру разрабатывали:', 'Какой-то мужик : Lixpan4ik (кодер)', 'Злодей-британец : Martin&Rose (художник)', 'Пубертатная язва : AlexMine2010 (помошник)', 'Бюджет игры: подзотыльник, 3 кириешки'], speed=3)
    dialog = Replic(['В дверь постучали...', '*тук* *тук* *тук*', 'Это оказались коллекторы.', 'Вы дали им денег.', 'Сверив сумму со счетчиком...'], speed=2.5) #2.5
    
    if player.balance >= manager.cost:
        dialog.replics.append('Они ушли...')
    else:
        dialog.replics.append('Вы были избиты...')

    global gamerun
    while gamerun:

        if keyboard.is_pressed('p'):
            Menu()

        screen.fill((0, 0, 0))
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gamerun = False
        
        dialog.Render(screen)

        if difficult >= 3 and dialog.finished:

            titres.Render(screen)

            if titres.finished:
                Menu()

        if difficult < 3:
            Menu()
        
        pygame.display.flip()

def Main():

    entrance_room = Scene((32*20, 32*9), list(screen_size), id=-2)
    other_entrance_room = Scene((32*20, 32*9), list(screen_size), id=-1)
    corridor_room = Scene((32*20, 32*9), list(screen_size), id=0)
    kitchen_room = Scene((32*14, 32*9), list(screen_size), id=1)
    bathroom_room = Scene((32*14, 32*9), list(screen_size), id=2)
    bedroom_room = Scene((32*14, 32*9), list(screen_size), id=3)

    corridor_room.addObject(Door(-20, corridor_room.size[1]-150, 40, 150, scene=kitchen_room))
    corridor_room.addObject(Door(corridor_room.size[0]-20, corridor_room.size[1]-150, 40, 150, scene=entrance_room))
    corridor_room.addObject(Door(100, corridor_room.size[1]-150, 100, 150, scene=bedroom_room))
    corridor_room.addObject(Door(250, corridor_room.size[1]-150, 100, 150, scene=bathroom_room))
    corridor_room.addObject(Object(420, corridor_room.size[1]-80, 160, 80, color=(10,10,10), texture=None))
    corridor_room.addObject(Phone(500, corridor_room.size[1]-80-40, 40, 40, (255, 255, 255)))
    #corridor_room.addObject(Phone(500, corridor_room.size[1]-80-40, 40, 40, (255, 255, 255))) Phone(500, corridor_room.size[1]-80-40, 40, 40, (255, 255, 255))
    corridor_room.addObject(Scoreboard(450, corridor_room.size[1]-65, 50, 50, color=(255, 255, 255)))

    kitchen_room.addObject(Door(kitchen_room.size[0]-20, kitchen_room.size[1]-150, 40, 150, scene=corridor_room))
    bathroom_room.addObject(Door(bathroom_room.size[0]-20, bathroom_room.size[1]-150, 40, 150, scene=corridor_room))
    bedroom_room.addObject(Door(bedroom_room.size[0]-20, bedroom_room.size[1]-150, 40, 150, scene=corridor_room))
    kitchen_room.addObject(Object(0, kitchen_room.size[1]-80, 280, 80, color=(10,10,10), texture=textures.shell))
    kitchen_room.addObject(Object(0, 20, 280, 90, color=(10,10,10), texture=textures.shell))
    bedroom_room.addObject(Object(0, bedroom_room.size[1]-80, 200, 80, color=(10,10,10), texture=textures.bed))
    bedroom_room.addObject(Object(240, bedroom_room.size[1]-70, 140, 70, color=(10,10,10), texture=None))
    bathroom_room.addObject(Object(20, bathroom_room.size[1]-80, 180, 80, color=(10,10,10), texture=textures.bath))
    bathroom_room.addObject(Object(260, bathroom_room.size[1]-70, 70, 80, color=(5,5,5), texture=textures.footwash))

    entrance_room.addObject(Door(20, entrance_room.size[1]-150, 100, 150, scene=corridor_room))
    entrance_room.addObject(Door(140, entrance_room.size[1]-150, 100, 150, canOpen=False, scene=None))
    entrance_room.addObject(Door(300, entrance_room.size[1]-170, 180, 170, scene=other_entrance_room, texture=textures.lift, texture_true=textures.lift_open))
    entrance_room.addObject(Npc(500, entrance_room.size[1]-140, 100, 140))

    other_entrance_room.addObject(Door(20, entrance_room.size[1]-150, 100, 150, canOpen=False, scene=None))
    other_entrance_room.addObject(Door(140, entrance_room.size[1]-150, 100, 150, canOpen=False, scene=None))
    other_entrance_room.addObject(Door(300, entrance_room.size[1]-170, 180, 170, scene=entrance_room, texture=textures.lift, texture_true=textures.lift_open))

    flags_group = [
        [1, FlagObject(290, 50, 120, 160, color=(10,10,10), texture=textures.window, texture_true=textures.open_window)],
        [1, FlagObject(30, kitchen_room.size[1]-80-50, 50, 50, color=(10,10,10), texture=textures.pipe, texture_true=textures.open_pipe)],
        [2, FlagObject(30, bathroom_room.size[1]-80, 30, 30, color=(10,10,10), texture=textures.pipe, texture_true=textures.open_pipe)],
        [2, FlagObject(280, bathroom_room.size[1]-70-25, 30, 30, color=(5,5,5), texture=textures.pipe, texture_true=textures.open_pipe)],
        [3, FlagObject(270, bedroom_room.size[1]-70-25, 60, 40, color=(10,10,10), texture=textures.notebook, texture_true=textures.open_notebook)],
        [3, FlagObject(50, 20, 120, 160, color=(10,10,10), texture=textures.window, texture_true=textures.open_window)]
    ]

    timer = Timer()
    manager = Manager()

    for i in range(random.randint(4, 6)):
        other_entrance_room.addObject(Wasted(random.randint(0, other_entrance_room.size[0]-40), entrance_room.size[1]-40, 40, 40))
    
    for i in range(random.randint(3, 5)):
        entrance_room.addObject(Wasted(random.randint(0, entrance_room.size[0]-40), entrance_room.size[1]-40, 40, 40))

    setTargetScene(corridor_room)

    player = Player(
        100,
        getTargetScene().size[1]-140,
        90,
        140
    )

    global gamerun
    while gamerun:
        
        if keyboard.is_pressed('p'):
            Menu()

        if timer.timer <= 0 and timer.timer != -1:
            EndCostScreen(player, manager)
        
        if timer.timer >= 0: timer.timer -= delta_time

        screen.fill((0, 0, 0))
        clock.tick(fps)

        _font = pygame.font.Font(None, 46)
        _color = (255, 0, 0) if timer.timer <= 10 else (255, 255, 255)
        _surf = _font.render(
            str(round(timer.timer))+' секунд',
            False, _color,
            (0, 0, 0)
        )
        if timer.timer >= 0: screen.blit(_surf, (0, screen_size[1]-_surf.get_height()))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gamerun = False
        
        pygame.draw.rect(
            screen,
            (
                20, 20, 20
            ),
            pygame.Rect(
                getTargetScene().position[0], 
                getTargetScene().position[1],
                getTargetScene().size[0],
                getTargetScene().size[1]
            )
        )

        for obj in getTargetScene().collection:
            obj(
                screen, getTargetScene(), player, manager, timer, flags_group
            )

        for obj in flags_group:
            if obj[0] == getTargetScene().id:
                obj[1](
                    screen, getTargetScene(), player, manager, timer, flags_group
                )

        player(screen, getTargetScene())

        manager(flags_group)
        
        pygame.display.flip()

if __name__ == '__main__':

    Menu()
