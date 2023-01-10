import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import datetime
from time import sleep
import memory
import videocard
import cpu


class OutputPortNotImplementedException(Exception):
    pass


class InputPortNotImplementedException(Exception):
    pass

class MotherBoard:
    def __init__(self):
        # All motherboards need memory and a CPU.  The CPU needs access to the motherboard to do I/O.
        self.memory = memory.Memory()
        self.cpu = cpu.I8080cpu(self)

    def handle_input(self, port):
        raise InputPortNotImplementedException("Input port {} not handled".format(port))

    def handle_output(self, port, data):
        raise OutputPortNotImplementedException("Output port {} not handled".format(port))


class Test8080SystemMotherBoard(MotherBoard):
    def __init__(self):
        super().__init__()
        self.memory = memory.Test8080SystemMemory()
        self.cpu.pc = 0x100  # CP/M programs load at 0x100

    def handle_output(self, port, data):
        if port == 0x0:
            print(chr(data), end='')
        else:
            raise OutputPortNotImplementedException("Output port {} not handled".format(port))

    def load_cpm_shim(self, shim):
        i = 0x0
        for byte in shim:
            self.memory[i] = byte
            i += 1


class SpaceInvadersMotherBoard(MotherBoard):
    def __init__(self):
        super().__init__()
        self.memory = memory.SpaceInvadersMemory()
        self.video_card = videocard.SpaceInvadersScreen(self)

        self.credit_pressed = False
        self.one_player_start_pressed = False
        self.two_player_start_pressed = False

        self.player_one_left_pressed = False
        self.player_one_fire_pressed = False
        self.player_one_right_pressed = False

        self.player_two_left_pressed = False
        self.player_two_fire_pressed = False
        self.player_two_right_pressed = False

        # DIPs 3 and 5 are read as two bits - 00 is 3 ships, 01 is 4, 10 is 5, 11 is 6.
        self.dip3 = True
        self.dip5 = False
        # DIP 6 controls whether extra ship is at 1500 (if 0) or 1000 (if 1)
        self.dip6 = True
        # DIP 7 controls whether coin info is displayed in the demo screen, 0 = On
        self.dip7 = False

        # Shift register
        # See: https://www.computerarcheology.com/Arcade/SpaceInvaders/Hardware.html#dedicated-shift-hardware
        self.shift_register = 0x0000
        self.shift_register_offset = 0

        # Sounds
        # Sounds sourced from: http://www.classicgaming.cc/classics/space-invaders/sounds except for extended play,
        # which was originally called 9.wav in the Space Invaders file at https://samples.mameworld.info/ (look at
        # "Unofficial Samples").  Sounds were generated from analog hardware and emulating that is painful, so
        # I am using samples.
        pygame.mixer.init()
        self.sound_ufo = pygame.mixer.Sound("sounds/ufo_lowpitch.wav")
        self.sound_shot = pygame.mixer.Sound("sounds/shoot.wav")
        self.sound_flash_player_die = pygame.mixer.Sound("sounds/explosion.wav")
        self.sound_invader_die = pygame.mixer.Sound("sounds/invaderkilled.wav")
        self.sound_extended_play = pygame.mixer.Sound("sounds/extended_play.wav")
        self.sound_fleet_movement_1 = pygame.mixer.Sound("sounds/fastinvader1.wav")
        self.sound_fleet_movement_2 = pygame.mixer.Sound("sounds/fastinvader2.wav")
        self.sound_fleet_movement_3 = pygame.mixer.Sound("sounds/fastinvader3.wav")
        self.sound_fleet_movement_4 = pygame.mixer.Sound("sounds/fastinvader4.wav")
        self.sound_ufo_hit = pygame.mixer.Sound("sounds/ufo_highpitch.wav")
        # Initialize to the time the game starts, so first time we try to play these sounds, it will have passed
        self.last_sound_shot_played = datetime.datetime.now()
        self.sound_shot_second_delay = 0.75
        self.last_sound_player_die_played = datetime.datetime.now()
        self.sound_player_die_second_delay = 3


    def handle_input(self, port):
        # see: https://www.walkofmind.com/programming/side/hardware.htm
        # Keep in mind - a bit for an input is enabled until they are processed by the CPU and then the
        # bit is disabled
        # Only 3 input ports are used
        # 1 - Coin slot, start game and player 1 controls
        # 2 - Game configuration and player 2 controls
        # 3 - Shift register
        if port == 0x1:
            ret_val = 0x08  # bit 3 is always pressed per computerarchaeology.com
            if self.credit_pressed:
                ret_val |= 0x01
            if self.two_player_start_pressed:
                ret_val |= 0x02
            if self.one_player_start_pressed:
                ret_val |= 0x04
            if self.player_one_fire_pressed:
                ret_val |= 0x10
            if self.player_one_left_pressed:
                ret_val |= 0x20
            if self.player_one_right_pressed:
                ret_val |= 0x40
            # bit 7 is ignored

            return ret_val

        elif port == 0x2:
            ret_val = 0x0
            if self.dip3:
                ret_val |= 0x01
            if self.dip5:
                ret_val |= 0x02
            if self.dip6:
                ret_val |= 0x08
            if self.player_two_fire_pressed:
                ret_val |= 0x10
            if self.player_two_left_pressed:
                ret_val |= 0x20
            if self.player_two_right_pressed:
                ret_val |= 0x40
            if self.dip7:
                ret_val |= 0x80

            return ret_val

        elif port == 0x3:
            tmp = self.shift_register
            tmp = (tmp >> (8 - self.shift_register_offset)) & 0xFF
            return tmp

        else:
            raise InputPortNotImplementedException(port)

    def handle_output(self, port, data):
        # All the CPU does for output is send the right byte to the right I/O port.  The work is done by the
        # motherboard.
        #
        # https://www.computerarcheology.com/Arcade/SpaceInvaders/Hardware.html#output
        # Port 2 - bits 0, 1, 2 are the amount of the shift - see "Dedicated Shift Hardware" on the above page
        # Port 3 - Sounds
        # Port 4 - shift data (LSB on 1st write, MSB on 2nd)
        # Port 5 - Sounds
        # Port 6 - Watchdog
        #

        if port == 0x2:
            self.shift_register_offset = data & 0x07
        elif port == 0x3:
            # https://www.computerarcheology.com/Arcade/SpaceInvaders/Hardware.html#output
            # bits 0-4 are sounds
            # bit 0 = UFO (repeats)
            # bit 1 = Shot
            # bit 2 = Flash (player die)
            # bit 3 = Invader die
            # bit 4 = Extended Play
            # bit 5 = AMP enable
            # bit 6, 7 = NC (not wired)
            if data & 0x1:
                self.sound_ufo.play()
            if data & 0x2:
                # This output is sent several times for each shot, but we only want to play the sound once
                curtime = datetime.datetime.now()
                tickdiff = (curtime - self.last_sound_shot_played).total_seconds()
                if tickdiff >= self.sound_shot_second_delay:
                    self.last_sound_shot_played = curtime
                    self.sound_shot.play()
            if data & 0x4:
                # This output is sent several times for each player death, but we only want to play the sound once
                curtime = datetime.datetime.now()
                tickdiff = (curtime - self.last_sound_player_die_played).total_seconds()
                if tickdiff >= self.sound_player_die_second_delay:
                    self.last_sound_player_die_played = curtime
                    self.sound_flash_player_die.play()
            if data & 0x8:
                self.sound_invader_die.play()
            if data & 0x10:
                self.sound_extended_play.play()
            if data & 0x20:
                # I believe that we should just ignore this because I think that "AMP enable" is for sound, but
                # will wait until/if this is encountered in the code before I figure it out.
                pass
        elif port == 0x4:
            self.shift_register = self.shift_register >> 8
            self.shift_register |= (data << 8)
        elif port == 0x5:
            # https://www.computerarcheology.com/Arcade/SpaceInvaders/Hardware.html#output
            # bits 0-4 are sounds
            # bits 0-3 = Fleet movement 1-4
            # bit 4 = UFO hit
            # bit 5 = flip screen in Cocktail mode - not implemented in this version
            # bits 6, 7 = NC (not wired)
            if data & 0x1:
                self.sound_fleet_movement_1.play()
            if data & 0x2:
                self.sound_fleet_movement_2.play()
            if data & 0x4:
                self.sound_fleet_movement_3.play()
            if data & 0x8:
                self.sound_fleet_movement_4.play()
            if data & 0x10:
                self.sound_ufo_hit.play()
        elif port == 0x6:
            # https://www.reddit.com/r/EmuDev/comments/rykj04/questions_about_watchdog_port_in_space_invaders/
            # Watchdog resets the entire machine if port 6 doesn't receive read/write requests every so many cycles.
            # For the purposes of our emulator, we can ignore it.
            pass
        else:
            raise OutputPortNotImplementedException(port)

    def debug_sound_test(self):
        for port in [3, 5]:
            for data in [0x1, 0x2, 0x4, 0x8, 0x10]:
                self.handle_output(port, data)
                sleep(3)
