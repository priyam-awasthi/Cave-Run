import asyncio
import pygame
import sys
# import time
from pygame import mixer
import os

mixer.init()

pygame.init()

screen_size = (1280, 720)
screen = pygame.display.set_mode(screen_size)

player1_sprite = pygame.image.load("images/C1_Still.png")
player1_sprite = player1_sprite.convert_alpha()

player2_sprite = pygame.image.load("images/C2_Still.png")
player2_sprite = player2_sprite.convert_alpha()

platform_sprite = pygame.image.load("images/platform.png")

checked_ins = True

completed_levels = ['level1']


async def level_ready(prev_level, level_list):
    if prev_level not in level_list:
        return False
    else:
        return True


# Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self, sprite, pos):
        super().__init__()
        self.rect = None
        self.gravity = 0.5
        self.friction = 0.85
        self.size = [17, 50]
        self.pos = pos
        self.sprite = sprite
        self.speed = [0, 0]
        self.on_ground = True
        self.colliding = False
        self.gem_counter = 0
        self.walking = False
        self.facing_left = False
        self.facing_right = True
        self.timer = 10

    def controls(self, left, right, up):
        pressed = pygame.key.get_pressed()
        if not self.colliding:
            if pressed[left]:
                self.pos[0] -= 0.5
                self.speed[0] -= 0.75
                self.walking = True
                self.facing_left = True
                self.facing_right = False
            if pressed[right]:
                self.pos[0] += 0.5
                self.speed[0] += 0.75
                self.walking = True
                self.facing_left = False
                self.facing_right = True
            if pressed[up] and self.on_ground:
                self.pos[1] -= 1
                self.speed[1] -= 11.25
                self.on_ground = False

            if not pressed[left] and not pressed[right]:
                self.walking = False
        # Apply gravity
        self.speed[1] += self.gravity
        self.speed[0] *= self.friction
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]
        self.rect = pygame.Rect(self.pos, self.size)



    def screen_border(self):
        if self.pos[0] < 0:
            self.pos[0] = 0
        elif self.pos[0] > screen_size[0] - self.size[0]:
            self.pos[0] = screen_size[0] - self.size[0]
        if self.pos[1] < 0:
            self.pos[1] = 0
            self.speed[1] = 0
            self.on_ground = False
        elif self.pos[1] > screen_size[1] - self.size[1]:
            self.pos[1] = screen_size[1] - self.size[1]
            self.speed[1] = 0
            self.on_ground = True

    def draw(self, base_sprite):
        base_sprite = "images/" + base_sprite

        if not self.on_ground and self.facing_right:
            base_sprite += "_Jump.png"
            self.sprite = pygame.image.load(base_sprite)
            screen.blit(self.sprite, self.pos)

        elif not self.on_ground and self.facing_left:
            base_sprite += "_Jump_Left.png"
            self.sprite = pygame.image.load(base_sprite)
            screen.blit(self.sprite, self.pos)

        elif self.on_ground and self.facing_right:
            base_sprite += ".png"
            self.sprite = pygame.image.load(base_sprite)
            screen.blit(self.sprite, self.pos)

        elif self.on_ground and self.facing_left:
            base_sprite += "_Left.png"
            self.sprite = pygame.image.load(base_sprite)
            screen.blit(self.sprite, self.pos)

    def walking_draw(self, base_name):
        for i in range(1, 5):
            self.timer += 0.2
            if self.timer // 10 == 5:
                self.timer = 10
            if self.facing_right:
                path_name = f"{base_name}{int(self.timer // 10)}.png"
            if self.facing_left:
                path_name = f"{base_name}{int(self.timer // 10)}{'_Left'}.png"
            player_sprite = pygame.image.load(path_name)
            player_sprite = player_sprite.convert_alpha()
            screen.blit(player_sprite, self.pos)


# Platform Class
class Platform(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, xsize):
        super().__init__()
        self.width = xsize
        self.length = 20
        self.pos = [xpos, ypos]
        self.size = [self.width, self.length]
        self.rect = pygame.Rect(self.pos, self.size)
        self.sprite = self.create_platform()

    def draw(self):
        screen.blit(self.sprite, self.pos)

    def platform_collision(self, player):
        if player.rect.colliderect(self.rect):
            player.colliding = True
            if self.rect.left + player.speed[0] < player.rect.right and player.rect.left - player.speed[0] \
                    < self.rect.right:
                if player.rect.centery < self.rect.centery:
                    player.rect.bottom = self.rect.top - 1
                    player.pos[1] = self.rect.top - player.size[1]
                    player.speed[1] = 0
                    player.on_ground = True
                else:
                    if player.speed[1] < 0:
                        player.speed[1] *= -2

            if player.rect.top + player.speed[1] < self.rect.bottom and self.rect.top - player.speed[1] \
                    < player.rect.bottom:
                player.speed[0] *= -2

        else:
            player.colliding = False

    def create_platform(self):
        sample = pygame.image.load(os.path.join(os.path.dirname(__file__), 'images/platform.png'))
        output_surface = pygame.surface.Surface((self.size[0], 20))

        for i in range(self.size[0] // 20):
            output_surface.blit(sample, (i * 20, 0))
        return output_surface


# Wall Class
class MovingWall(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, width, limit, buttons):
        super().__init__()
        self.original_ypos = ypos
        self.pos = [xpos, ypos]
        self.size = [width, 12]
        self.rect = pygame.Rect(self.pos, self.size)

        self.sprite = self.create_platform()

        # Moving
        self.limit_pos = ypos - limit
        self.buttons = buttons

    def collision(self, player):
        self.rect = pygame.Rect(self.pos, self.size)
        if player.rect.colliderect(self.rect):
            if self.rect.left + player.speed[0] < player.rect.right and player.rect.left - player.speed[0] \
                    < self.rect.right:
                if player.rect.centery < self.rect.centery:
                    player.rect.bottom = self.rect.top - 1
                    player.pos[1] = self.rect.top - player.size[1]
                    player.speed[1] = 0
                    player.on_ground = True
                else:
                    if player.speed[1] < 0:
                        player.speed[1] *= -2

            if player.rect.top + player.speed[1] < self.rect.bottom and self.rect.top - player.speed[1] \
                    < player.rect.bottom:
                player.speed[0] *= -2.5

        else:
            player.colliding = False

    def check_buttons(self):
        buttons_pressed = [button for button in self.buttons if button.pressed]
        if len(buttons_pressed) == 1 or len(buttons_pressed) == 2:
            self.move_up()
        else:
            self.return_to_origin()

    def move_up(self):
        if self.limit_pos < self.pos[1]:
            self.pos[1] -= 2

    def return_to_origin(self):
        if self.pos[1] < self.original_ypos:
            self.pos[1] += 2

    def create_platform(self):
        sample = pygame.image.load(os.path.join(os.path.dirname(__file__), 'images/moving_platform.png'))
        output_surface = pygame.surface.Surface(self.size)

        for i in range(self.size[0] // 20):
            output_surface.blit(sample, (i * 20, 0))
        return output_surface

    def draw(self):
        screen.blit(self.sprite, self.pos)


# Button Class

class Button(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos):
        super().__init__()
        self.original_ypos = ypos
        self.pos = [xpos, ypos]
        self.size = [20, 10]
        self.rect = pygame.Rect(self.pos, self.size)
        self.pressed = False
        self.up_sprite = pygame.image.load("images/button-up.png")
        self.down_sprite = pygame.image.load("images/button-down.png")
        self.up_sprite = self.up_sprite.convert_alpha()
        self.down_sprite = self.down_sprite.convert_alpha()

    def collision(self, players):
        players_pressing = []
        for player in players:
            if player.rect.colliderect(self.rect):
                players_pressing.append(player)

        if len(players_pressing) == 1 or len(players_pressing) == 2:
            self.pressed = True
            if not (self.pos[1] - self.original_ypos == 4):
                self.pos[1] += 0.5
        else:
            self.pressed = False
            if not (self.pos[1] == self.original_ypos):
                self.pos[1] -= 0.5

    def draw(self):
        self.rect = pygame.Rect(self.pos, self.size)
        if self.pressed:
            screen.blit(self.down_sprite, self.pos)
        else:
            screen.blit(self.up_sprite, self.pos)


# Gem Class
class Gem(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, sprite):
        super().__init__()
        self.sprite_name = sprite
        self.sprite = pygame.image.load(sprite)
        self.sprite = self.sprite.convert_alpha()
        self.pos = [xpos, ypos]
        self.size = 20
        self.collected = False
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.sprite.get_height(), self.sprite.get_width())

    def draw(self):
        if not self.collected:
            screen.blit(self.sprite, self.pos)

    def player_gem_collect(self, player):
        if player.rect.colliderect(self.rect) and not self.collected:
            player.gem_counter += 1
            gem_sound = mixer.Sound("gem_sound.ogg")
            pygame.mixer.Sound.set_volume(gem_sound, 0.2)
            gem_sound.play()
            self.collected = True


# Background Class
class Background(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location


# Goal Class
class Goal(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos):
        super().__init__()
        self.pos = [xpos, ypos]
        self.size = [70, 74]
        self.rect = pygame.Rect(self.pos, self.size)
        self.sprite = "images/exit/exit"
        self.timer = 10
        self.exit_ready = False
        self.open = False

    def check_exit(self, gems, player1, player2):
        if player1.rect.colliderect(self.rect) and player2.rect.colliderect(self.rect):
            if len(gems) == player1.gem_counter + player2.gem_counter:
                self.exit_ready = True

    def draw(self):
        if self.exit_ready:
            if self.timer // 10 == 6:
                self.timer = 10

            elif self.image_path == "images/exit/exit5.png":
                self.open = True
            else:
                self.sprite = "images/exit/exit"
                self.image_path = "images/exit/exit" + str(int(self.timer // 10)) + ".png"
                self.timer += 0.35
        else:
            self.image_path = "images/exit/exit1.png"

        self.sprite = pygame.image.load(self.image_path)
        self.sprite = self.sprite.convert_alpha()
        screen.blit(self.sprite, self.pos)

    def exit_level(self, player1_up, player2_up):
        pressed = pygame.key.get_pressed()
        if self.open:
            if pressed[player1_up] and pressed[player2_up]:
                return True
        else:
            return False


async def levels_complete_popup():
    font = pygame.font.SysFont("calibri", 35)
    level_access = font.render("Complete the previous levels first!", True, (0, 0, 0))
    level_access_pos = (355, 250)

    level_access_exit = font.render("Cancel", True, (0, 0, 0))
    level_access_exit_pos = (575, 400)

    box_rect = pygame.Rect(325, 250, 600, 225)
    x_button_pos = list(box_rect.topleft)
    x_button_pos[1] -= 10
    x_button_text = font.render("x", True, (0, 0, 0))

    x_button_rect = pygame.Surface.get_rect(x_button_text)
    x_button_rect.topleft = box_rect.topleft

    level_access_exit_rect = level_access_exit.get_rect()
    level_access_exit_rect.topleft = level_access_exit_pos

    pygame.draw.rect(screen, (255, 255, 255), box_rect)

    screen.blit(level_access_exit, level_access_exit_pos)
    screen.blit(level_access, level_access_pos)
    screen.blit(x_button_text, x_button_pos)
    pygame.display.update()
    pop_up = True

    while pop_up:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if x_button_rect.collidepoint(pygame.mouse.get_pos()) or level_access_exit_rect.collidepoint(
                        pygame.mouse.get_pos()):
                    print(state, '-> level_menu')
                    return level_menu()

        await asyncio.sleep(0)


clock = pygame.time.Clock()


async def level1():
    pygame.mouse.set_visible(False)
    # Create a platform rectangle
    plat1 = Platform(0, 605, 960)
    plat2 = Platform(320, 490, 960)
    plat3 = Platform(0, 380, 960)
    plat4 = Platform(480, 210, 960)

    background = Background('images/Background1.png', [0, 0])

    button1 = Button(640, 370)
    button2 = Button(525, 200)

    wall = MovingWall(240, 300, 60, 50, [button1, button2])

    # Player 1
    player = Player(player1_sprite, [20, 720])

    # Player 2
    player2 = Player(player2_sprite, [80, 720])

    platforms = [plat1, plat2, plat3, plat4]

    gem1 = Gem(640, 550, "images/gem1.png")
    gem2 = Gem(100, 550, "images/gem2.png")
    gem3 = Gem(250, 200, "images/gem1.png")
    gem4 = Gem(850, 350, "images/gem2.png")

    level_end = Goal(850, 140)

    gems = [gem1, gem2, gem3, gem4]

    # -------- Main Program Loop -----------
    done = False
    while not done:

        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        # Get the current keys pressed
        player.controls(pygame.K_a, pygame.K_d, pygame.K_w)
        player2.controls(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP)
        # Platform collision check
        for platform in platforms:
            platform.platform_collision(player)

        for platform in platforms:
            platform.platform_collision(player2)

        for gem in gems:
            if gem.sprite_name == "images/gem2.png":
                gem.player_gem_collect(player2)
            if gem.sprite_name == 'images/gem1.png':
                gem.player_gem_collect(player)

        # Check for collision with the border of the screen

        player.screen_border()
        player2.screen_border()



        wall.collision(player)
        wall.collision(player2)

        button1.collision([player, player2])
        button2.collision([player, player2])

        wall.check_buttons()

        level_end.check_exit(gems, player, player2)

        if level_end.exit_level(pygame.K_UP, pygame.K_w):
            completed_levels.append('level1')
            print(state, ' -> level_menu')
            return level_menu()

        # Draw The Background
        screen.blit(background.image, background.rect)

        # Draw the player sprite
        button1.draw()
        button2.draw()
        wall.draw()

        for plat in platforms:
            plat.draw()

        for gem in gems:
            gem.draw()

        # screen.blit(await update_fps(), (10, 0))
        level_end.draw()
        if player.walking and player.on_ground:
            player.walking_draw("images/C1_Walk")
        else:
            player.draw("C1_Still")

        if player2.walking and player2.on_ground:
            player2.walking_draw("images/C2_Walk")
        else:
            player2.draw("C2_Still")

        # --- Go ahead and update the screen.
        clock.tick(60)
        pygame.display.update()
        await asyncio.sleep(0)


async def level2():
    pygame.mouse.set_visible(False)
    # Create a platform rectangle
    background = Background('images/Background2.png', [0, 0])

    # Player 1
    player = Player(player1_sprite, [620, 720])

    # Player 2
    player2 = Player(player2_sprite, [660, 720])

    plat1 = Platform(158, 600, 380)
    plat2 = Platform(742, 600, 380)
    plat3 = Platform(158, 430, 380)
    plat4 = Platform(742, 430, 380)
    plat5 = Platform(158, 260, 380)
    plat6 = Platform(742, 260, 380)
    plat7 = Platform(480, 170, 280)

    gem1 = Gem(310, 660, "images/gem1.png")
    gem2 = Gem(910, 660, "images/gem2.png")
    gem3 = Gem(310, 530, "images/gem2.png")
    gem4 = Gem(910, 530, "images/gem1.png")
    gem5 = Gem(310, 360, "images/gem1.png")
    gem6 = Gem(910, 360, "images/gem2.png")
    gem7 = Gem(310, 190, "images/gem2.png")
    gem8 = Gem(910, 190, "images/gem1.png")

    button1 = Button(780, 710)
    button2 = Button(500, 710)
    button3 = Button(495, 160)
    button4 = Button(725, 160)

    wall1 = MovingWall(1175, 650, 100, 390, [button1, button3])
    wall2 = MovingWall(5, 650, 100, 390, [button2, button4])

    level_end = Goal(575, 100)

    gems = [gem1, gem2, gem3, gem4, gem5, gem6, gem7, gem8]
    platforms = [plat1, plat2, plat3, plat4, plat5, plat6, plat7]

    # -------- Main Program Loop -----------
    done = False
    while not done:
        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        # Get the current keys pressed
        player.controls(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP)
        player2.controls(pygame.K_a, pygame.K_d, pygame.K_w)

        # Check for collision with the border of the screen
        player.screen_border()
        player2.screen_border()

        # platform collision player1
        for plat in platforms:
            plat.platform_collision(player)

        # platform collision player2
        for plat in platforms:
            plat.platform_collision(player2)

        # gem collision
        for gem in gems:
            if gem.sprite_name == "images/gem1.png":
                gem.player_gem_collect(player)
            if gem.sprite_name == "images/gem2.png":
                gem.player_gem_collect(player2)

        # button collision
        button1.collision([player, player2])
        button2.collision([player, player2])
        button3.collision([player, player2])
        button4.collision([player, player2])

        # wall1 collision
        wall1.collision(player)
        wall1.collision(player2)

        # wall2 collision
        wall2.collision(player)
        wall2.collision(player2)

        # wall check buttons for movement
        wall1.check_buttons()
        wall2.check_buttons()

        level_end.check_exit(gems, player, player2)

        if level_end.exit_level(pygame.K_UP, pygame.K_w):
            completed_levels.append('level2')
            print(state, ' -> level_menu')
            return level_menu()

        # Draw The Background
        screen.blit(background.image, background.rect)

        # Draw the player sprite

        # screen.blit(await update_fps(), (10, 0))

        for plat in platforms:
            plat.draw()

        for gem in gems:
            gem.draw()

        button1.draw()
        button2.draw()
        button3.draw()
        button4.draw()

        wall1.draw()
        wall2.draw()

        level_end.draw()

        if player.walking and player.on_ground:
            player.walking_draw("images/C1_Walk")
        else:
            player.draw("C1_Still")

        if player2.walking and player2.on_ground:
            player2.walking_draw("images/C2_Walk")
        else:
            player2.draw("C2_Still")

        # --- Go ahead and update the screen.
        clock.tick(60)
        pygame.display.update()
        await asyncio.sleep(0)


async def level3():
    pygame.mouse.set_visible(False)
    # Create a platform rectangle
    background = Background('images/Background1.png', [0, 0])

    # Player 1
    player = Player(player1_sprite, [20, 720])

    # Player 2
    player2 = Player(player2_sprite, [80, 720])

    plat1 = Platform(143, 625, 140)
    plat2 = Platform(470, 575, 140)
    plat3 = Platform(785, 525, 140)
    plat4 = Platform(1095, 475, 120)
    plat5 = Platform(810, 390, 140)
    plat6 = Platform(510, 340, 140)
    plat7 = Platform(210, 290, 140)
    plat8 = Platform(250, 125, 160)
    plat9 = Platform(575, 175, 160)
    plat10 = Platform(875, 125, 160)

    platforms = [plat1, plat2, plat3, plat4, plat5, plat6, plat7, plat8, plat9, plat10]

    button1 = Button(1200, 710)
    button2 = Button(1015, 115)
    buttons = [button1, button2]

    wall1 = MovingWall(0, 300, 100, 125, buttons)

    level_end = Goal(610, 105)

    gem1 = Gem(525, 660, "images/gem1.png")
    gem2 = Gem(190, 575, "images/gem2.png")
    gem3 = Gem(835, 475, "images/gem1.png")
    gem4 = Gem(1135, 415, "images/gem2.png")
    gem5 = Gem(555, 285, "images/gem1.png")
    gem6 = Gem(15, 50, "images/gem2.png")
    gem7 = Gem(310, 75, "images/gem1.png")
    gem8 = Gem(935, 75, "images/gem2.png")

    gems = [gem1, gem2, gem3, gem4, gem5, gem6, gem7, gem8]

    # -------- Main Program Loop -----------
    done = False
    while not done:

        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        # Get the current keys pressed
        player.controls(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP)
        player2.controls(pygame.K_a, pygame.K_d, pygame.K_w)

        # Check for collision with the border of the screen
        player.screen_border()
        player2.screen_border()

        # Platform Collision
        for plat in platforms:
            plat.platform_collision(player)

        for plat in platforms:
            plat.platform_collision(player2)

        # Wall collision
        wall1.collision(player)
        wall1.collision(player2)

        # Wall Movement
        wall1.check_buttons()

        # Exit code
        level_end.check_exit(gems, player, player2)

        if level_end.exit_level(pygame.K_UP, pygame.K_w):
            completed_levels.append('level3')
            print(state, ' -> level_menu')
            return level_menu()

        # Button Collision
        for button in buttons:
            button.collision([player, player2])

        # Gem Collision
        for gem in gems:
            if gem.sprite_name == "images/gem2.png":
                gem.player_gem_collect(player2)
            if gem.sprite_name == 'images/gem1.png':
                gem.player_gem_collect(player)

        # Draw The Background
        screen.blit(background.image, background.rect)

        # screen.blit(await update_fps(), (10, 0))

        # Draw Gems
        for gem in gems:
            gem.draw()

        # Draw Walls
        wall1.draw()

        # Draw Buttons
        for button in buttons:
            button.draw()

        # Draw Exit
        level_end.draw()

        # Draw Platform
        for plat in platforms:
            plat.draw()

        # Draw Player
        if player.walking and player.on_ground:
            player.walking_draw("images/C1_Walk")
        else:
            player.draw("C1_Still")

        if player2.walking and player2.on_ground:
            player2.walking_draw("images/C2_Walk")
        else:
            player2.draw("C2_Still")

        # FPS and Screen Update
        clock.tick(60)
        pygame.display.update()
        await asyncio.sleep(0)


async def level4():
    pygame.mouse.set_visible(False)

    # Create a background
    background = Background('images/Background2.png', [0, 0])

    # Player 1
    player = Player(player1_sprite, [20, 720])

    # Player 2
    player2 = Player(player2_sprite, [80, 720])

    plat1 = Platform(250, 420, 100)
    plat2 = Platform(450, 305, 100)
    plat3 = Platform(700, 200, 200)
    plat4 = Platform(700, 300, 200)
    plat5 = Platform(700, 400, 200)
    plat6 = Platform(700, 500, 200)
    plat7 = Platform(1050, 300, 200)
    plat8 = Platform(1050, 400, 200)
    plat9 = Platform(1050, 500, 200)
    plat10 = Platform(1050, 200, 200)
    plat11 = Platform(235, 155, 180)

    platforms = [plat1, plat2, plat3, plat4, plat5, plat6, plat7, plat8, plat9, plat10, plat11]

    gem1 = Gem(633, 650, "images/gem1.png")
    gem2 = Gem(278, 375, "images/gem2.png")
    gem3 = Gem(775, 150, "images/gem1.png")
    gem4 = Gem(1140, 150, "images/gem2.png")
    gem5 = Gem(775, 250, "images/gem2.png")
    gem6 = Gem(1140, 250, "images/gem1.png")
    gem7 = Gem(775, 350, "images/gem1.png")
    gem8 = Gem(1140, 350, "images/gem2.png")
    gem9 = Gem(775, 450, "images/gem2.png")
    gem10 = Gem(1140, 450, "images/gem1.png")

    gems = [gem1, gem2, gem3, gem4, gem5, gem6, gem7, gem8, gem9, gem10]

    button1 = Button(640, 710)
    button2 = Button(1150, 190)
    button3 = Button(375, 145)
    buttons = [button1, button2, button3]

    wall1 = MovingWall(100, 600, 85, 75, buttons)
    wall2 = MovingWall(600, 160, 85, 100, buttons)

    walls = [wall1, wall2]

    level_end = Goal(270, 85)

    done = False
    while not done:

        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        # Get the current keys pressed
        player.controls(pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP)
        player2.controls(pygame.K_a, pygame.K_d, pygame.K_w)

        # Check for collision with the border of the screen
        player.screen_border()
        player2.screen_border()

        for plat in platforms:
            plat.platform_collision(player)

        for plat in platforms:
            plat.platform_collision(player2)

        for button in buttons:
            button.collision([player, player2])

        for wall in walls:
            wall.collision(player)
            wall.collision(player2)

        for wall in walls:
            wall.check_buttons()

        level_end.check_exit(gems, player, player2)

        if level_end.exit_level(pygame.K_UP, pygame.K_w):
            completed_levels.append('level4')
            print(state, ' -> level_menu')
            return level_menu()

        for gem in gems:
            if gem.sprite_name == "images/gem2.png":
                gem.player_gem_collect(player2)
            if gem.sprite_name == 'images/gem1.png':
                gem.player_gem_collect(player)

        # Draw Background
        screen.blit(background.image, background.rect)

        for plat in platforms:
            plat.draw()

        for gem in gems:
            gem.draw()

        for button in buttons:
            button.draw()

        for wall in walls:
            wall.draw()

        level_end.draw()

        # Draw player
        if player.walking and player.on_ground:
            player.walking_draw("images/C1_Walk")
        else:
            player.draw("C1_Still")

        if player2.walking and player2.on_ground:
            player2.walking_draw("images/C2_Walk")
        else:
            player2.draw("C2_Still")

        clock.tick(45)
        pygame.display.update()
        await asyncio.sleep(0)


async def start_menu():
    pygame.mouse.set_visible(True)
    menu_done = False
    screen.fill((0, 0, 0))

    title_font = pygame.font.SysFont("calibri", 100)
    title = title_font.render("Cave Run", True, (255, 255, 255))
    screen.blit(title, (450, 50))

    background = Background('images/CoverBackground.png', [0, 0])
    screen.blit(background.image, background.rect)
    screen.blit(title, (100, 50))

    button_font = pygame.font.SysFont("calibri", 35)
    start_button = button_font.render("Start Game", True, (255, 255, 255))
    start_button_pos = (770, 365)
    screen.blit(start_button, start_button_pos)

    instructions_button = button_font.render("How To Play?", True, (255, 255, 255))
    instructions_button_pos = (770, 535)
    screen.blit(instructions_button, instructions_button_pos)

    levels_screen = False
    while not menu_done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Get the coordinates of the mouse cursor
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if start_button_pos[0] < mouse_x < start_button_pos[0] + 200 and start_button_pos[1] < mouse_y < \
                        start_button_pos[1] + 50 and not levels_screen:
                    screen.fill((0, 0, 0))
                    print(state, "->level_menu")
                    return level_menu()
                if instructions_button_pos[0] < mouse_x < instructions_button_pos[0] + 200 and instructions_button_pos[
                    1] \
                        < mouse_y < instructions_button_pos[1] + 50 and not levels_screen:
                    screen.fill((0, 0, 0))
                    print(state, "-> instructions screen")
                    return instructions()
        pygame.display.update()
        await asyncio.sleep(0)


async def level_menu():
    pygame.mouse.set_visible(True)
    global state
    global checked_ins

    background = Background('images/LevelScreenBackground.png', [0, 0])

    screen.blit(background.image, background.rect)

    button_font = pygame.font.SysFont("calibri", 35)
    level_1_button = button_font.render("Level 1", True, (255, 255, 255))
    level_1_pos = (250, 200)

    level_1_rect = level_1_button.get_rect()
    level_1_rect.topleft = level_1_pos

    level_2_button = button_font.render("Level 2", True, (255, 255, 255))
    level_2_pos = (930, 200)

    level_2_rect = level_2_button.get_rect()
    level_2_rect.topleft = level_2_pos

    level_3_button = button_font.render("Level 3", True, (255, 255, 255))
    level_3_pos = (250, 500)

    level_3_rect = level_3_button.get_rect()
    level_3_rect.topleft = level_3_pos

    level_4_button = button_font.render("Level 4", True, (255, 255, 255))
    level_4_pos = (930, 500)

    level_4_rect = level_4_button.get_rect()
    level_4_rect.topleft = level_4_pos

    back_button_levels = button_font.render("Back", True, (255, 255, 255))
    back_button_pos_levels = (50, 100)

    back_rect = back_button_levels.get_rect()
    back_rect.topleft = back_button_pos_levels

    level_screen = True
    if not checked_ins:
        warning_text = button_font.render("Please Check on 'How to Play' First to learn the controls!",
                                          True,
                                          (255, 255, 255))
        back_button = button_font.render("Back", True, (255, 255, 255))

        back_button_pos = (50, 50)
        warning_text_pos = (200, 320)

        screen.blit(warning_text, warning_text_pos)
        screen.blit(back_button, back_button_pos)
        pygame.display.update()

        while level_screen:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if back_button_pos[0] < mouse_x < back_button_pos[0] + 100 and back_button_pos[1] < mouse_y < \
                            back_button_pos[1] + 50:
                        print(state, "-> start_menu")
                        return start_menu()
            await asyncio.sleep(0)

    if checked_ins:
        screen.blit(level_1_button, level_1_pos)
        screen.blit(level_2_button, level_2_pos)
        screen.blit(level_3_button, level_3_pos)
        screen.blit(level_4_button, level_4_pos)
        screen.blit(back_button_levels, back_button_pos_levels)
        pygame.display.update()

        while level_screen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if level_1_rect.collidepoint((mouse_x, mouse_y)):
                        print(state, "->level1")
                        return level1()

                    if level_2_rect.collidepoint((mouse_x, mouse_y)):
                        if not await level_ready("level1", completed_levels):
                            print(state, "->level_completion_popup")
                            return levels_complete_popup()
                        else:
                            print(state, "->level2")
                            return level2()

                    if level_3_rect.collidepoint((mouse_x, mouse_y)):
                        if not await level_ready("level2", completed_levels):
                            print(state, "-> level_completion_popup")
                            return levels_complete_popup()
                        else:
                            print(state, "-> level3")
                            return level3()
                    if level_4_rect.collidepoint((mouse_x, mouse_y)):
                        if not await level_ready("level3", completed_levels):
                            print(state, "-> level_completion_popup")
                            return levels_complete_popup()
                        else:
                            print(state, "-> level4")
                            return level4()

                    if back_rect.collidepoint((mouse_x, mouse_y)):
                        print(state, "-> start_menu")
                        return start_menu()

            pygame.display.update()
            await asyncio.sleep(0)


async def instructions():
    pygame.mouse.set_visible(True)
    global state
    global checked_ins
    button_font = pygame.font.SysFont("calibri", 35)
    back_button = button_font.render("Back", True, (255, 255, 255))
    back_button_pos = (50, 50)

    ins_font = pygame.font.SysFont("calibri", 25)

    player1_gems = ins_font.render("The Red Gems are for Bob!", True, (255, 255, 255))
    player1_gems_pos = (75, 500)

    player2_gems = ins_font.render("The Blue Gems are for Joe!", True, (255, 255, 255))
    player2_gems_pos = (900, 500)

    exit_ins = button_font.render("To exit the level, both player must press their up buttons at the same time!", True,
                                  (255, 255, 255))
    exit_ins2 = button_font.render("But remember, you have to collect all of your gems first!", True, (255, 255, 255))
    exit_ins_pos = (45, 600)
    exit_ins2_pos = (180, 650)

    background = Background("images/howtoplay.png", [0, 0])
    screen.blit(background.image, background.rect)

    screen.blit(back_button, back_button_pos)

    screen.blit(exit_ins, exit_ins_pos)
    screen.blit(exit_ins2, exit_ins2_pos)
    screen.blit(player1_gems, player1_gems_pos)
    screen.blit(player2_gems, player2_gems_pos)

    ins_screen = True

    checked_ins = True
    while ins_screen:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if back_button_pos[0] < mouse_x < back_button_pos[0] + 100 and back_button_pos[1] < mouse_y < \
                        back_button_pos[1] + 50:
                    print(state, "-> start_menu")
                    return start_menu()
        pygame.display.update()
        await asyncio.sleep(0)


mixer.music.load('song_new.ogg')
mixer.music.set_volume(0.2)
mixer.music.play(-1)


async def main():
    global state
    # Set the title of the window
    pygame.display.set_caption("Cave Run")

    state = start_menu()
    while state:
        state = await state
        await asyncio.sleep(0)

    # Close the window and quit.
    pygame.quit()
    sys.exit()


asyncio.run(main())
