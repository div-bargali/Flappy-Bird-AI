import pygame
import neat
import time
import os
import random
pygame.font.init() # init font

WIN_WIDTH = 500
WIN_HEIGHT = 800
DRAW_LINES = True

GEN = 0



BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
            pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
            pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -9.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        if d >= 16: # terminal dist
            # d = d / abs(d) * 16
            d = 16
        if d < 0:
            d -= 2

        self.y += d

        if d < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION: # don't overshoot MAX_ROTATION
                self.tilt = self.MAX_ROTATION
        else: # tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL # as we go more down tilt more
        
    def draw(self, win): # window
        self.img_count += 1

        # wings flapping animation 
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80: # when the bird is falling, render only one image
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # rotate image around center based on tilt angle
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft= (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0 
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        # set the height of the pipe, from the top of the screen

        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # how far away the bird_mask and top_mask and bird_mask and bottom_mask are
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True
        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.WIDTH + self.x2

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.WIDTH + self.x1

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    # draw window

    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))   

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))  
    
    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    base.draw(win)

    for bird in birds:
        if DRAW_LINES is True:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x + bird.img.get_width() / 2, bird.y +
                                 bird.img.get_height() / 2), (pipes[pipe_ind].x +
                                 pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height), 3)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + 
                                 bird.img.get_height()/2), (pipes[pipe_ind].x +
                                 pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 3)
            except:
                pass
        bird.draw(win) # draw bird
    pygame.display.update()

# def draw_pause_screen(win, base, score):
#     win.blit(BG_IMG, (0, 0))

#     text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
#     win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

#     base.draw(win)
#     pygame.display.update()

# def pause_screen(win, base, score):
#     clock = pygame.time.Clock()
#     run = True

#     while(run):
#         clock.tick(30)
#         win.blit(BG_IMG, (0, 0))
#         for event in pygame.event.get():
#             keys = pygame.key.get_pressed()
#             if keys[pygame.K_SPACE]:
#                 run = False
#                 return False

#             if keys[pygame.K_t]:
#                 run = False
#                 return True
            
#             if event.type == pygame.QUIT:
#                 run = False
#                 pygame.QUIT()
#                 quit()
#         base.move()
#         draw_pause_screen(win, base, score)

# def draw_game_screen(win, birds, pipes, base, score):
#     win.blit(BG_IMG, (0, 0))

#     for pipe in pipes:
#         pipe.draw(win)

#     text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
#     win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))   

#     base.draw(win)

#     for bird in birds:
#         bird.draw(win) # draw bird
#     pygame.display.update()

# def mainUtil(genomes, config):
    
#     while True:
#         base = Base(730)

#         birds = []
#         birds.append(Bird(230, 350))
        
#         pipes = [Pipe(600)]

#         win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
#         score = high_score = 0


#         train_state = pause_screen(win, base , high_score)
#         if train_state:
#             while True:
#                 main(genomes, config)

#         clock = pygame.time.Clock()
#         run = True

#         while run:
#             clock.tick(30)
#             for event in pygame.event.get():
#                 keys = pygame.key.get_pressed()
#                 if keys[pygame.K_SPACE]:
#                     bird.jump()
#                 if event.type == pygame.QUIT:
#                     run = False
#                     pygame.QUIT()
#                     quit()

#             pipe_ind = 0
#             if len(birds) > 0:
#                 if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
#                     # if the bird has passed the 0th index pipe in the list pipes
#                     pipe_ind = 1
#             else:
#                 run = False
#                 break 

#             for x, bird in enumerate(birds):
#                 bird.move()

#             #bird.move()
#             add_pipe = False
#             rem = []
#             for pipe in pipes:
#                 for x, bird in enumerate(birds):
#                     if pipe.collide(bird):
#                         # favour birds that don't hit the pipe and made it to the same 
#                         # distance then remove the bird and stop tracking it

#                         birds.pop(x)
                        

#                     if not pipe.passed and pipe.x < bird.x: # if bird has passed the pipe
#                         pipe.passed = True
#                         add_pipe = True

#                 if pipe.x + pipe.PIPE_TOP.get_width() < 0:
#                     # if the pipe is out of the screen
#                     # add it to rem
#                     rem.append(pipe)

#                 pipe.move()

#             if add_pipe:
#                 score += 1
#                 pipes.append(Pipe(600))

#             for r in rem:
#                 # remove all pipes out of the screen
#                 pipes.remove(r)

#             for x, bird in enumerate(birds):
#                 # check if the bird hits the base/ground
#                 # or goes over the screen 
#                 if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
#                     birds.pop(x)

#             base.move()
#             draw_game_screen(win, birds, pipes, base, score)

#         high_score = max(score, high_score)

def main(genomes, config):
    # fitness function for NEAT
    # also the main function

    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []
    
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config) # setup a neural network
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0


    run = True
    while run:
        clock.tick(45)
        for event in pygame.event.get():
            # keys = pygame.key.get_pressed()
            # if keys[pygame.K_j]:
            #     bird.jump()
            if event.type == pygame.QUIT:
                run = False
                pygame.QUIT()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                # if the bird has passed the 0th index pipe in the list pipes
                pipe_ind = 1
        else:
            run = False
            break 

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y , abs(bird.y - pipes[pipe_ind].top), abs(bird.y -
                                        pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        #bird.move()
        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # favour birds that don't hit the pipe and made it to the same 
                    # distance then remove the bird and stop tracking it

                    ge[x].fitness -= 1 
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x: # if bird has passed the pipe
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                # if the pipe is out of the screen
                # add it to rem
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            for g in ge:
                # reward birds that made it through a pipe without colliding 
                g.fitness += 5 
            score += 1
            pipes.append(Pipe(600))

        for r in rem:
            # remove all pipes out of the screen
            pipes.remove(r)

        for x, bird in enumerate(birds):
            # check if the bird hits the base/ground
            # or goes over the screen 
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN, pipe_ind)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
             neat.DefaultSpeciesSet, neat.DefaultStagnation,
             config_path)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)

if __name__ == "__main__":
    # load config files and pass them to run fucntion

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)


