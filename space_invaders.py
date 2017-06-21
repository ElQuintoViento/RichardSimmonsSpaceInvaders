#!/usr/local/bin/python3
from time import time
import pygame


#
SECONDS_TO_MICRO_SECONDS = 1000000
#
TUPLE_COLOR_BLACK = (0, 0, 0)
TUPLE_COLOR_GREEN = (0, 226, 143)
TUPLE_COLOR_RED = (226, 70, 70)
#
IMAGE_BIG_MAC = "big_mac_small.png"
IMAGE_RICHARD_SIMMONS = "richard_simmons_small_2.png"
# Frames per second
TIME_TICK_LOOP = 120
#
MARGIN_SCREEN = 20
MARGIN_OPPONENTS = MARGIN_SCREEN + 105
HEIGHT_SCREEN = 720
WIDTH_SCREEN = 1080
LENGTH_BOX_SHIP = 50
# Player frame
HEIGHT_FRAME_PLAYER = max(
    HEIGHT_SCREEN // 10, LENGTH_BOX_SHIP)
WIDTH_FRAME_PLAYER = WIDTH_SCREEN
WIDTH_FRAME_PLAYER_HALF = WIDTH_FRAME_PLAYER // 2
# Opponent frame
FACTOR_HEIGHT_FRAME_OPPONENTS = 1.0 / 2.0
HEIGHT_FRAME_OPPONENTS = (
    HEIGHT_SCREEN - HEIGHT_FRAME_PLAYER)
WIDTH_FRAME_OPPONENTS = WIDTH_SCREEN
#
ACCELERATION_VALUE_MAX = 50
ACCELERATION_INCREMENT_HUMAN = 10
ACCELERATION_MULTIPLIER = 2.5
DECCELERATION_FACTOR = 0.85
INCREMENT_MOVE_X_OPPONENT = 10
INCREMENT_MOVE_Y_OPPONENT = 30
#
COUNT_COLUMN_AND_ROW_OPPONENT = 7
#
DIRECTION_NONE = -1
DIRECTION_LEFT = 0
DIRECTION_RIGHT = 1
DIRECTION_UP = 2
DIRECTION_DOWN = 3
#
WINNER_NONE = -1
WINNER_HUMAN = 0
WINNER_OPPONENT = 1


def sign(value):
    if value == 0:
        return 0
    return int(abs(value) / value)


class BasicSprite:
    def __init__(self, screen, sprite, rect):
        self.create_random_id()
        self.screen = screen
        self.sprite = sprite
        self.rect = rect
        self.update_dimensions()
        self.update_mask()
        self.set_exists(True)

    # Assigns an id using current time in microseconds
    def create_random_id(self):
        self.id = int(time() * SECONDS_TO_MICRO_SECONDS)

    # Ensures destroyed object won't be redrawn; however, object needs to be
    # removed externally (i.e. where it is stored)
    def destroy(self):
        self.set_exists(False)

    def update_rect(self):
        self.rect = self.sprite.get_rect()

    def update_dimensions(self):
        self.dimensions = self.sprite.get_size()

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.sprite)
        #print("\nmask {}\n".format(self.mask.__dir__()))

    def get_mask(self):
        return self.mask

    def get_coordinates(self):
        return (
            self.rect.left,
            self.rect.right,
            self.rect.top,
            self.rect.bottom)

    # Distance between left side and left side of screen
    def get_left_gap(self):
        return self.rect.left

    # Distance between right side and right side of screen
    def get_right_gap(self):
        return (WIDTH_SCREEN - self.rect.right)

    def exists(self):
        return self._exists

    # Determine if two sprites overlap/collide
    def check_overlaps(self, basic_sprite):
        value = self.mask.overlap(
            basic_sprite.get_mask(),
                (basic_sprite.rect.left - self.rect.left,
                    basic_sprite.rect.top - self.rect.top))
        return value

    def set_exists(self, exists):
        self._exists = exists

    # Move to position unless outside of allowed coordinates; returns actual
    # position delta in contrast with asked
    def set_location(self, x, y):
        center_change = [
            self.rect.centerx,
            self.rect.centery]
        self.rect.centerx = x
        self.rect.centery = y
        # Ensure within allowed coordinates
        if self.rect.left < MARGIN_SCREEN:
            self.rect.centerx = MARGIN_SCREEN + self.dimensions[0] // 2
        elif self.rect.right > (WIDTH_SCREEN - MARGIN_SCREEN):
            self.rect.centerx = (
                (WIDTH_SCREEN - MARGIN_SCREEN) - self.dimensions[0] // 2)
        # Return true position delta
        center_change[0] = self.rect.centerx - center_change[0]
        center_change[1] = self.rect.centery - center_change[1]
        return center_change

    # Scale sprite to box container (max_dimension X max_dimension)
    def scale_to_fit(self, max_dimension):
        scale_factor = (
            float(max_dimension) / float(max(*self.dimensions)))
        width = int(float(self.dimensions[0]) * scale_factor)
        height = int(float(self.dimensions[1]) * scale_factor)
        self.sprite = pygame.transform.scale(self.sprite, (width, height))
        self.update_rect()
        self.update_dimensions()
        self.update_mask()

    # Translate by some delta ensuring to stay within allowed range
    def translate(self, x, y):
        return self.set_location(self.rect.centerx + x, self.rect.centery + y)

    # Only redraw if 'exists'
    def redraw(self):
        if self.exists():
            self.screen.blit(self.sprite, self.rect)
        return self.exists()


class Background(BasicSprite):
    def __init__(self, screen):
        super().__init__(
            screen,
            pygame.Surface(screen.get_size()),
            (0, 0))
        self.sprite.fill(TUPLE_COLOR_BLACK)


# Simple Text Label
class Text(BasicSprite):
    def __init__(self, screen, text, color, font, size):
        self.text = text
        self.color = color
        self.font = font
        self.size = size
        self.my_font = pygame.font.SysFont(font, size)
        self.label = self.my_font.render(text, 1, color)
        super().__init__(
            screen,
            self.label,
            self.label.get_rect())


# Base spaceship
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
        self.scale_to_fit(LENGTH_BOX_SHIP)
        # default location
        self.set_location(0, 0)


class HumanSpaceShip(SpaceShip):
    def __init__(self, screen):
        super().__init__(screen, IMAGE_RICHARD_SIMMONS, TUPLE_COLOR_GREEN)
        # Floor division set to middle
        self.set_location(WIDTH_SCREEN / 2, HEIGHT_SCREEN / 2)
        # Set 0 acceleration
        self.acceleration = [0, 0]

    # Center within allowed human coordinates
    def center(self):
        x = WIDTH_FRAME_PLAYER / 2
        y = (
            HEIGHT_SCREEN -
            (HEIGHT_FRAME_PLAYER / 2))
        self.set_location(x, y)

    # Accelerate in only -/+ x direction; inhibit acceleration while
    # approaching sides
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

    # Decrement acceleration to inhibit continuous movement
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


# Handles all opponent space ships
class OpponentSquadron:
    def __init__(self, screen, row_and_column_size):
        self.direction = DIRECTION_RIGHT
        self.direction_previous = self.direction
        self.screen = screen
        self.row_and_column_size = row_and_column_size
        self.ships = {}
        self.left = {}
        self.right = {}
        self.front_line = {}
        self.setup_ships()

    # Return front ships
    def get_front_line_ships(self):
        return self.front_line

    # Evenly space out ships within initial allowed range
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

    # Check whether left or right ships reached allowed edge/coordinates
    def check_reached_boundary(self):
        ships = self.left
        if self.direction == DIRECTION_RIGHT:
            ships = self.right
        ship = list(ships.values())[0]
        #
        gap = MARGIN_SCREEN * 2
        if self.direction == DIRECTION_RIGHT:
            gap = ship.get_right_gap()
        else:
            gap = ship.get_left_gap()
        #
        return (gap <= MARGIN_SCREEN)

    # Update which direction ships are flying in
    def update_direction(self):
        tmp_direction = self.direction
        # Currently moving left
        if ((self.direction == DIRECTION_LEFT) or
                (self.direction == DIRECTION_RIGHT)):
            if self.check_reached_boundary():
                self.direction = DIRECTION_DOWN
                self.direction_previous = tmp_direction
        # Switch to left or right?
        elif self.direction == DIRECTION_DOWN:
            if self.direction_previous == DIRECTION_LEFT:
                self.direction = DIRECTION_RIGHT
            else:
                self.direction = DIRECTION_LEFT
            self.direction_previous = tmp_direction

    # Calculate translation delta and move
    def move_ships(self):
        translation = [0, 0]
        #
        self.update_direction()
        #
        if self.direction == DIRECTION_LEFT:
            translation = [-1 * INCREMENT_MOVE_X_OPPONENT, 0]
        elif self.direction == DIRECTION_RIGHT:
            translation = [INCREMENT_MOVE_X_OPPONENT, 0]
        elif self.direction == DIRECTION_DOWN:
            translation = [0, INCREMENT_MOVE_Y_OPPONENT]
        #
        '''
        ships_to_move = {
            id: ship
            for id, ship in ships_to_move.items() if ship not in ships_moved}
        '''
        #for id, ship in ships_to_move.items():
        for id, ship in self.ships.items():
            ship.translate(translation[0], translation[1])

    def update(self):
        self.move_ships()
        for id, ship in self.ships.items():
            ship.redraw()
            # print("{} coords: {}".format(ship.id, ship.get_coordinates()))


class Game:
    def __init__(self):
        pygame.init()
        self.init_winner()
        self.init_screen()
        self.init_human_ship()
        self.init_opponent_squadron()

    def init_winner(self):
        self.winner = WINNER_NONE
        self.winner_text = None

    def init_screen(self):
        self.screen = pygame.display.set_mode(
            (WIDTH_SCREEN, HEIGHT_SCREEN))
        self.background = Background(self.screen)

    def init_human_ship(self):
        self.human_ship = HumanSpaceShip(self.screen)
        self.human_ship.center()

    def init_opponent_squadron(self):
        self.opponent_squadron = OpponentSquadron(
            self.screen, COUNT_COLUMN_AND_ROW_OPPONENT)

    def check_collisions(self):
        if self.human_ship is not None:
            collided = False
            ships = self.opponent_squadron.get_front_line_ships().items()
            for id, ship in ships:
                if self.human_ship.check_overlaps(ship):
                    ship.destroy()
                    collided = True
            #
            if collided:
                self.human_ship.destroy()

    def clean_up(self):
        if self.human_ship is not None:
            if not self.human_ship.exists():
                self.human_ship = None

    def update_winner(self):
        if self.winner == WINNER_NONE:
            text = None
            color = None
            if self.human_ship is None:
                self.winner = WINNER_OPPONENT
                text = "Opponent"
                color = TUPLE_COLOR_RED
            elif self.opponent_squadron is None:
                self.winner = WINNER_HUMAN
                text = "Human"
                color = TUPLE_COLOR_GREEN
            else:
                self.winner = WINNER_NONE
            #
            if self.winner != WINNER_NONE:
                text = "{} Wins!".format(text)
                self.winner_text = Text(
                    self.screen, text, color, "arial", 60)
                self.winner_text.set_location(
                    WIDTH_SCREEN // 2, HEIGHT_SCREEN // 2)

    def update(self):
        self.background.redraw()
        #
        self.update_winner()
        if self.winner == WINNER_NONE:
            #
            self.check_collisions()
            self.clean_up()
            if self.human_ship is not None:
                self.human_ship.redraw()
            self.opponent_squadron.update()
        else:
            self.winner_text.redraw()
        # Update display
        pygame.display.flip()

    def handle_key_pressed(self):
        if self.human_ship is not None:
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
        self.update()
        self.clock = pygame.time.Clock()
        while True:
            # Frames per second
            self.clock.tick(TIME_TICK_LOOP)
            pygame.event.pump()
            self.handle_key_pressed()
            self.handle_events()
            self.update()


def main():
    game = Game()
    game.loop()


if __name__ == '__main__':
    main()
