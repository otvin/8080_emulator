import pygame
import datetime

SCALE_FACTOR = 1
PIXEL_OFF = (0, 0, 0)
PIXEL_ON = (255, 255, 255)


class SpaceInvadersScreen:
    # 1 bit per pixel - other 8080-based games had better graphics
    def __init__(self, motherboard, xsize=256, ysize=224):
        self.motherboard = motherboard
        self.xsize = xsize
        self.ysize = ysize
        self.window = pygame.display.set_mode((self.xsize * SCALE_FACTOR, self.ysize * SCALE_FACTOR))
        pygame.display.set_caption("Fred's i8080 Emulator")
        # For performance, so we do not have to dereference these pointers constantly
        self.vram = motherboard.memory
        self.vram_start = motherboard.memory.vram_start
        self.window.fill(0)
        self.num_renders = 0
        self.render_time_ps = 0
        self.draw_rect_list = []
        self.clear()
        self.needs_draw = False
        self.last_draw_time = datetime.datetime.now()

    def clear(self):
        for i in range(self.xsize * self.ysize // 8):
            self.vram[self.vram_start + i] = 0
        self.draw_rect_list.append((0, 0, self.xsize, self.ysize))
        self.draw()

    def setpx(self, x, y, val):
        pass

    def draw(self):
        pass



