#!/usr/local/bin/python3
from time import time
import pygame

#
TUPLE_COLOR_BLACK = (0, 0, 0)
TUPLE_COLOR_GREEN = (0, 226, 143)
TUPLE_COLOR_RED = (226, 70, 70)
#
IMAGE_BIG_MAC = "big_mac_small.png"
IMAGE_RICHARD_SIMMONS = "richard_simmons_small_2.png"
#
TIME_TICK_LOOP = 120
#
MARGIN_SCREEN = 20
MARGIN_OPPONENTS = MARGIN_SCREEN + 55
HEIGHT_SCREEN = 720
WIDTH_SCREEN = 1080
LENGTH_BOX_SHIP = 50
# Player frame
HEIGHT_FRAME_PLAYER = max(
    HEIGHT_SCREEN // 10, LENGTH_BOX_SHIP)
WIDTH_FRAME_PLAYER = WIDTH_SCREEN
WIDTH_FRAME_PLAYER_HALF = WIDTH_FRAME_PLAYER // 2
# Opponent frame
FACTOR_HEIGHT_FRAME_OPPONENTS = 1.0 / 2.25
HEIGHT_FRAME_OPPONENTS = (
    HEIGHT_SCREEN - HEIGHT_FRAME_PLAYER)
WIDTH_FRAME_OPPONENTS = WIDTH_SCREEN
#
ACCELERATION_VALUE_MAX = 50
ACCELERATION_INCREMENT_HUMAN = 10
ACCELERATION_MULTIPLIER = 2.5
DECCELERATION_FACTOR = 0.85
#
SECONDS_TO_MICRO_SECONDS = 1000000
#
OPPONENT_COUNT_COLUMN_AND_ROW = 5


def sign(value):
    if value == 0:
        return 0
    return int(abs(value) / value)


class BasicSprite:
    def __init__(self, screen, sprite, rect):
        self.create_random_id()
        self.screen = screen
        self.sprite = sprite
        self.dimensions = sprite.get_size()
        self.rect = rect

    def create_random_id(self):
        self.id = int(time() * SECONDS_TO_MICRO_SECONDS)

    def get_coordinates(self):
        return (
            self.rect.left,
            self.rect.right,
            self.rect.top,
            self.rect.bottom)

    def set_location(self, x, y):
        self.rect.centerx = x
        self.rect.centery = y
        #
        if self.rect.left < MARGIN_SCREEN:
            self.rect.centerx = MARGIN_SCREEN + self.dimensions[0] // 2
        elif self.rect.right > (WIDTH_SCREEN - MARGIN_SCREEN):
            self.rect.centerx = (
                (WIDTH_SCREEN - MARGIN_SCREEN) - self.dimensions[0] // 2)

    def translate(self, x, y):
        self.set_location(self.rect.centerx + x, self.rect.centery + y)

    def redraw(self):
        self.screen.blit(self.sprite, self.rect)


class Background(BasicSprite):
    def __init__(self, screen):
        super().__init__(
            screen,
            pygame.Surface(screen.get_size()),
            (0, 0))
        self.sprite.fill(TUPLE_COLOR_BLACK)


class SpaceShip(BasicSprite):
    def __init__(self, screen, ship_image, default_square_color):
        # Attempt to load image
        try:
            sprite = pygame.image.load(ship_image)
        # Create rect instead
        except Exception as e:
            print("{}\nLoading default square".format(e))
            sprite = pygame.Surface((LENGTH_BOX_SHIP, LENGTH_BOX_SHIP))
            # Set color
            sprite.fill(default_square_color)
        super().__init__(screen, sprite, sprite.get_rect())
        self.set_max_dimension()
        # default location
        self.set_location(0, 0)

    def set_max_dimension(self):
        scale_factor = (
            float(LENGTH_BOX_SHIP) / float(max(*self.dimensions)))
        width = int(float(self.dimensions[0]) * scale_factor)
        height = int(float(self.dimensions[1]) * scale_factor)
        self.sprite = pygame.transform.scale(self.sprite, (width, height))
        self.rect = self.sprite.get_rect()
        self.dimensions = self.sprite.get_size()


class HumanSpaceShip(SpaceShip):
    def __init__(self, screen):
        super().__init__(screen, IMAGE_RICHARD_SIMMONS, TUPLE_COLOR_GREEN)
        # Floor division set to middle
        self.set_location(WIDTH_SCREEN / 2, HEIGHT_SCREEN / 2)
        # Set 0 acceleration
        self.acceleration = [0, 0]

    def center(self):
        x = WIDTH_FRAME_PLAYER / 2
        y = (
            HEIGHT_SCREEN -
            (HEIGHT_FRAME_PLAYER / 2))
        self.set_location(x, y)

    def accelerate(self, x, y):
        # X
        self.acceleration[0] += x
        gap = WIDTH_FRAME_PLAYER_HALF
        if sign(self.acceleration[0]) > 0:
            gap = (
                WIDTH_FRAME_PLAYER -
                self.rect.centerx -
                self.dimensions[0] // 2)
        elif sign(self.acceleration[0]) < 0:
            gap = (
                self.rect.centerx -
                self.dimensions[0] +
                self.dimensions[0] // 2)
        gap = int(float(gap) * 0.75)
        limit_x = min(
            int(ACCELERATION_VALUE_MAX *
                gap * ACCELERATION_MULTIPLIER / WIDTH_FRAME_PLAYER),
            ACCELERATION_VALUE_MAX)
        self.acceleration[0] = (
            sign(self.acceleration[0]) *
            min(abs(self.acceleration[0]), limit_x))
        # Y - Unfinished since restricted y-movement
        self.acceleration[1] += y
        self.acceleration[1] = (
            sign(self.acceleration[1]) *
            min(self.acceleration[1], ACCELERATION_VALUE_MAX))

    def deccelerate(self):
        if abs(self.acceleration[0]) > 0:
            self.acceleration[0] = int(
                float(self.acceleration[0]) * DECCELERATION_FACTOR)
        if abs(self.acceleration[1]) > 0:
            self.acceleration[1] = int(
                float(self.acceleration[1]) * DECCELERATION_FACTOR)

    def redraw(self):
        self.translate(self.acceleration[0], self.acceleration[1])
        super(SpaceShip, self).redraw()
        self.deccelerate()


class OpponentSpaceShip(SpaceShip):
    def __init__(self, screen):
        super().__init__(screen, IMAGE_BIG_MAC, TUPLE_COLOR_RED)
        # Floor division set to middle
        self.set_location(WIDTH_SCREEN / 2, HEIGHT_SCREEN / 2)


class OpponentSquadron:
    def __init__(self, screen, row_and_column_size):
        self.screen = screen
        self.row_and_column_size = row_and_column_size
        self.ships = {}
        self.left = {}
        self.right = {}
        self.front_line = {}
        self.setup_ships()

    def setup_ships(self):
        start_bottom_edge = int(
            float(HEIGHT_FRAME_OPPONENTS) * FACTOR_HEIGHT_FRAME_OPPONENTS)
        horizontal_separation = (
            (WIDTH_SCREEN - (2 * MARGIN_OPPONENTS)) / self.row_and_column_size)
        vertical_separation = start_bottom_edge / self.row_and_column_size
        for r in range(0, self.row_and_column_size):
            for c in range(0, self.row_and_column_size):
                ship = OpponentSpaceShip(self.screen)
                id = ship.id
                x = int(
                    (0.5 + float(r)) * horizontal_separation +
                    MARGIN_OPPONENTS)
                y = int((0.5 + float(c)) * vertical_separation)
                ship.set_location(x, y)
                if r == 0:
                    self.left[id] = ship
                if r == (self.row_and_column_size - 1):
                    self.right[id] = ship
                if c == (self.row_and_column_size - 1):
                    self.front_line[id] = ship
                self.ships[id] = ship

    def redraw(self):
        for id, ship in self.ships.items():
            ship.redraw()
            # print("{} coords: {}".format(ship.id, ship.get_coordinates()))


class Game:
    def __init__(self):
        pygame.init()
        self.init_screen()
        self.init_human_ship()
        self.init_opponent_squadron()

    def init_screen(self):
        self.screen = pygame.display.set_mode(
            (WIDTH_SCREEN, HEIGHT_SCREEN))
        self.background = Background(self.screen)

    def init_human_ship(self):
        self.human_ship = HumanSpaceShip(self.screen)
        self.human_ship.center()

    def init_opponent_squadron(self):
        self.opponent_squadron = OpponentSquadron(
            self.screen, OPPONENT_COUNT_COLUMN_AND_ROW)

    def redraw(self):
        self.background.redraw()
        self.human_ship.redraw()
        self.opponent_squadron.redraw()
        # Update display
        pygame.display.flip()

    def handle_key_pressed(self):
        # Get key input
        key_input = pygame.key.get_pressed()
        #
        if key_input[pygame.K_LEFT]:
            self.human_ship.accelerate(-1 * ACCELERATION_INCREMENT_HUMAN, 0)
        elif key_input[pygame.K_RIGHT]:
            self.human_ship.accelerate(ACCELERATION_INCREMENT_HUMAN, 0)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)

    def loop(self):
        self.redraw()
        self.clock = pygame.time.Clock()
        while True:
            self.clock.tick(TIME_TICK_LOOP)
            pygame.event.pump()
            self.handle_key_pressed()
            self.handle_events()
            self.redraw()


def main():
    game = Game()
    game.loop()


if __name__ == '__main__':
    main()
