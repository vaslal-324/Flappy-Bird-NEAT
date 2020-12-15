import pygame
import neat  # NeuroEvluation of Augmenting Topologies
import random
import os
import time

#pop_size was changed to 20 because we don't want to test the wrong neural networks and make the birds
#leran by evolution

# config file is important for NEAT

pygame.font.init()

# Objects for the bird, the pipe, the floor
# while loop run rate is 30 FPS
WIN_WIDTH = 500
WIN_HEIGHT = 800  # POTRAIT
GEN =0

BIRD_IMGS = []
PIPE_IMG = pygame.transform.scale2x(pygame.image.load("pipe.png"))
BASE_IMG = pygame.transform.scale2x(pygame.image.load("base.png"))
BG_IMG = pygame.transform.scale2x(pygame.image.load("bg.png"))

STAT_FONT = pygame.font.SysFont("comicsans", 50)

for i in range(1, 4):
    BIRD_IMGS.append(pygame.transform.scale2x(pygame.image.load("bird" + str(i) + ".png")))


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
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5  # as the bird needs to move up
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1  # only for initial values of tick_count , the bird flies up (d is -ve),
        # for the rest of the counts , d becomes positive , so the bird falls down

        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2  # displacement = ut + 1/2 gt^2
        if d >= 16:  # displacement is postive while moving down, that is we add positive number to y coordinate
            d = 16  # Don't increase the displacement as the y corrdinate changes to a very large extent

        if d < 0:
            d -= 2  # to make the bird move in the upward direction a bit faster
        # the d = 16 and d-=2 were calculated by Tim when he had created the game ,
        # can tweak and see these numbers as well

        self.y += d

        # The above lines were for changing the y coordinates

        # Now, for rotational motion, how should the bird be titled
        # positive number for rotating up and negative number for rotating down
        if d < 0 or self.y < self.height + 50:  # going upwards, self.height stores the position where the bird jumps
            if self.tilt < self.MAX_ROTATION:  # directly change the rotation to 25 px
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt >= -90:  # it is not pointing down yet
                self.tilt -= self.ROT_VEL  # we don't use MAX_ROTATION because we want much greater rotation while
                # going down

    def draw(self, win):  # draws the bird with flapping wings
        self.img_count += 1  # executed everytime in the infinite loop

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        else:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:  # when the bird is diving down
            self.img = self.IMGS[1]  # The bird should not flap it's wings
            self.img_count = self.ANIMATION_TIME * 2  # by seeing the above if condition
            # when we don't update the image count , the image_count is reset to 0 in previous if stmts
            # so we'll get only IMG[0] which is not a levelled one

        # rotates the image but with pivot as topleft
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        # for rotating the image around the center
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        # making the center of the rotated image same as center of the straight image - the above line
        win.blit(rotated_image, new_rect.topleft)  # the blit coordinates start from topleft

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5  # we have to make the screen move backward as the bird does not move

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        # False for horizontal flip and True for vertical flip
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)  # start, stop and step are the parameters
        self.top = self.height - self.PIPE_TOP.get_height()  # since we need the topleft coordinate in pygame
        # we need to subtract the heights inorder to get negative weight or lift the pipe up randomly
        self.bottom = self.height + self.GAP

    def move(self):  # same x coordinate for both the top and the bottom pipe
        self.x -= self.VEL

    def draw(self, win):  # each pipe object draws two pipes
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
        # pygame.display.update()  # was not there in his code

    def collide(self, bird):
        # masks are used for pixel perfect collisions
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)  # returns a 2D list of all the pixels covered
        # by the image , wiht this we can check for collision
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        # offsets can be negative
        # Returns the point of intersection if the masks
        # overlap with the given offset - or "None" if it does not overlap.
        # Mask.overlap(othermask, offset) -> x,y

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False


# Tip :
# each class has an __init__() with necessary param passed(like coordinates), move() , draw() etc

class Base:  # base also moves back like the pipe
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):  # coordinates are passed for blitting
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH  # any variable inside the class when accessed , must be done as self.variable_name

    def move(self):
        self.x1 -= self.VEL  # velocity is just a change in pixels
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# to continue from base class

def draw_window(win, birds, pipes, base, score, gen):  # window and a bird object
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:  # many pipes are there on the screen
        pipe.draw(win)

    text = STAT_FONT.render("SCORE: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))  # since the laptop is 13" 10px from top cannot be seen

    text = STAT_FONT.render("GEN: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):  # 2 parameters of fitness function is genomes- bunch of neural networks and config file
    global GEN
    GEN +=1
    nets = []
    ge = []
    birds = []  # initial coordinates of the bird as mentioned by the __init__()

    for _, g in genomes: # as each g is a tuple with genome id and the genome oblject bur we care only for genome object
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]  # contains max two pipes , actually has the number of pipes(set of) visible on the screen
    run = True
    clock = pygame.time.Clock()
    score = 0

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # giving the coordinate as a tuple for pygame window

    while run:
        clock.tick(30)  # 30 fps ..we are controlling the motion of the bird instead of the infinite loop
        # default frame rate which depends on the computer
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()  # quit pygame
                quit()  # quitting the program

        pipe_ind = 0 # this is to account if the bird is moving towards the first or the second pipe
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): # can take even bird[1] or any other
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness +=0.1 # increasing the fitness only by 0.1 when the bird is alive, being alive is not
                                #significant as compared to passing the pipe
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5 : #output is a list, but here we have only one o/p neuron
                bird.jump()

        # bird.move()
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):  # enumerate fn returns the index also
                if pipe.collide(bird):  # collide() is implemented using masks
                    ge[x].fitness -= 1
                    birds.pop(x)
                    ge.pop(x)
                    nets.pop(x)  # pop( removes an elt when the index is supplied

                if not pipe.passed and pipe.x < bird.x:  # the bird has passed the pipe
                    pipe.passed = True
                    add_pipe = True  # we have to add a new pipe
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:  # the pipe has moved out of screen
                rem.append(pipe)
            pipe.move()
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))  # contains only a single pipe set in the list

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:  # if the bird has hit the ground or moves out of top window
                birds.pop(x)  # removing the bird entirely
                ge.pop(x)
                nets.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)





def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)  # loading the config file
    p = neat.Population(config)  # set up the population

    p.add_reporter(neat.StdOutReporter(True))  # for providing stats like fitness level etc
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)  # fitness function, max number of generations
    # calls the main() 50 times passing the current genomes/population ans the config file


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)  # both main.py and the config-feedforward.txt file are in same directory
    config_path = os.path.join(local_dir, "config-feedforward.txt")  # for finding the exact path of the config file
    run(config_path)
