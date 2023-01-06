import pygame
import datetime

SCALE_FACTOR = 1
PIXEL_OFF = (0, 0, 0)
PIXEL_ON = (255, 255, 255)

def color_from_pos_in_byte(byte, pos):
    global PIXEL_ON, PIXEL_OFF
    if (byte >> pos) & 1:
        return PIXEL_ON
    else:
        return PIXEL_OFF


class SpaceInvadersScreen:
    # 1 bit per pixel - other 8080-based games had better graphics
    def __init__(self, motherboard, xsize=224, ysize=256):
        self.motherboard = motherboard
        self.xsize = xsize
        self.ysize = ysize
        self.window = pygame.display.set_mode((self.xsize * SCALE_FACTOR, self.ysize * SCALE_FACTOR))
        pygame.display.set_caption("Fred's i8080 Emulator")
        # For performance, so we do not have to dereference these pointers constantly
        self.vram = motherboard.memory
        self.vram_start = motherboard.memory.vram_start
        self.vram_end = self.vram_start + (self.xsize * self.ysize // 8) - 1
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
        # see http://computerarcheology.com/Arcade/SpaceInvaders/Hardware.html or
        # https://www.walkofmind.com/programming/side/hardware.htm for some descriptions of the screen geometry
        x = 0
        y = 255
        mem_pos = self.vram_start
        byte = self.vram[mem_pos]
        while mem_pos <= self.vram_end:
            self.window.set_at((x, y), color_from_pos_in_byte(byte, 7 - (y % 8)))
            y -= 1
            if y < 0:
                y = 255
                x += 1
            if y % 8 == 0:
                mem_pos += 1
                byte = self.vram[mem_pos]
        pygame.display.update()

