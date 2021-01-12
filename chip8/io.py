import pygame

DEFAULT_KEY_MAP = {
    pygame.K_3: 0x1,
    pygame.K_4: 0x2,
    pygame.K_5: 0x3,
    pygame.K_6: 0xC,
    pygame.K_e: 0x4,
    pygame.K_r: 0x5,
    pygame.K_t: 0x6,
    pygame.K_y: 0xD,
    pygame.K_d: 0x7,
    pygame.K_f: 0x8,
    pygame.K_g: 0x9,
    pygame.K_h: 0xE,
    pygame.K_c: 0xA,
    pygame.K_v: 0x0,
    pygame.K_b: 0xB,
    pygame.K_n: 0xF
}


class PyGameKeyboard:
    def __init__(self, key_map=DEFAULT_KEY_MAP):
        self.key_pressed = [0] * 16   # array to store key status 0x0 to 0xF
        self.key_map = key_map

    def key_reader(self):
        """
        Read the keyboard and put the status of the keys into the key_pressed array
        :return:
        """
        keys = pygame.key.get_pressed()
        for k, v in self.key_map.items():
            self.key_pressed[v] = keys[k]

    def is_pressed(self, k):
        return self.key_pressed[k]

    def wait_for_key(self, callbacks=[]):
        """
        Waits for a key to be pressed, and once one is, returns its code.
        Run callbacks every checking loop (these should be fast to run)
        :return: code of the pressed key
        """
        pygame.event.clear()
        while True:
            # the timeout will give the callbacks a chance to run
            event = pygame.event.wait(timeout=10)
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key in self.key_map:
                    return self.key_map[event.key]

            for callback in callbacks:
                callback()

class PyGameScreen:
    WIDTH = 64
    HEIGHT = 32

    COLOR_ON = (205, 205, 255)
    COLOR_OFF = (0, 0, 0)


    def __init__(self, scale=10):
        self.buffer = [0] * self.WIDTH * self.HEIGHT
        self.scale = scale
        self.screen = pygame.display.set_mode([self.WIDTH * self.scale,
                                               self.HEIGHT * self.scale])

    def clear(self):
        """
        Clears the screen buffer
        :return:
        """
        self.buffer = [0] * self.WIDTH * self.HEIGHT
        #self.screen.fill(self.COLOR_OFF)
        #pygame.display.flip()

    def draw(self):
        self.screen.fill(self.COLOR_OFF)
        for x in range(self.WIDTH):
            for y in range(self.HEIGHT):
                #color = self.COLOR_ON if self.get(x, y) else self.COLOR_OFF
                #pygame.draw.rect(self.screen,
                #                 rect=pygame.Rect(x * self.scale,
                #                                  y * self.scale,
                #                                  self.scale - 1,
                #                                  self.scale - 1),
                #                                  color=color)
                if self.get(x, y):
                    pygame.draw.circle(self.screen,
                                       center=(x * self.scale + int(self.scale / 2),
                                               y * self.scale + int(self.scale / 2)),
                                       radius=int(self.scale / 2) + 2,
                                       color=self.COLOR_ON)
        pygame.display.flip()

    def get(self, x, y):
        """
        Get the value of the screen (buffer) at (x, y)
        :param x:
        :param y:
        :return:
        """
        return self.buffer[(y % self.HEIGHT) * self.WIDTH + (x % self.WIDTH)]

    def set(self, x, y, v):
        """
        Set the value of the screen buffer at (x, y) to v.  v must be 0 or 1
        :param x:
        :param y:
        :param v:
        :return:
        """
        if v > 1:
            raise ValueError("Screen values must be 0 or 1; got {}".format(v))
        self.buffer[(y % self.HEIGHT) * self.WIDTH + (x % self.WIDTH)] = v
