import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
from time import sleep
import pygame
import datetime
import disassembler
import debugger
import memory
import videocard
import cpu


class OutputPortNotImplementedException(Exception):
    pass


class InputPortNotImplementedException(Exception):
    pass


class SpaceInvadersMotherBoard:
    def __init__(self):
        self.memory = memory.SpaceInvadersMemory()
        self.video_card = videocard.SpaceInvadersScreen(self)
        self.cpu = cpu.I8080cpu(self)  # The CPU needs to access the motherboard to get to graphics, sound, and memory.
        self.stack_pointer_start = 0x2400  # needed for debugger to display the stack.  The SP itself gets set in code.

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

            # reset pressed buttons
            self.credit_pressed = False
            self.two_player_start_pressed = False
            self.one_player_start_pressed = False
            self.player_one_fire_pressed = False
            self.player_one_left_pressed = False
            self.player_one_right_pressed = False

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

            # reset pressed buttons
            self.player_two_fire_pressed = False
            self.player_two_left_pressed = False
            self.player_two_right_pressed = False

            return ret_val

        elif port == 0x3:
            raise InputPortNotImplementedException(port)
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

        if port == 0x3:
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
                self.sound_shot.play()
            if data & 0x4:
                self.sound_flash_player_die.play()
            if data & 0x8:
                self.sound_invader_die.play()
            if data & 0x10:
                self.sound_extended_play.play()
            if data & 0x20:
                # I believe that we should just ignore this because I think that "AMP enable" is for sound, but
                # will wait until/if this is encountered in the code before I figure it out.
                raise OutputPortNotImplementedException("Bit 5 of Port 3")
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

def main():

    debug_mode = False
    pygame.init()
    motherboard = SpaceInvadersMotherBoard()

    if len(sys.argv) >= 2:
        if sys.argv[1].lower() in ['-?', '-h', '-help']:
            print('Usage: python3 space_invaders [options]')
            print('Options include:')
            print('-h, -help, -?  = this list')
            print('-debug = start in the debugger')
            print('-soundtest = test sounds, then exit\n')
            sys.exit()
        elif sys.argv[1].lower() == '-debug':
            debug_mode = True
        elif sys.argv[1].lower() == '-soundtest':
            motherboard.debug_sound_test()
            sys.exit()
        else:
            print('Invalid option: {}'.format(sys.argv[1]))
            print('try "python3 space_invaders -?" for help\n')
            sys.exit()

    run = True

    start_time = datetime.datetime.now()
    num_states = 0
    num_instructions = 0
    last_instruction_time = datetime.datetime.now()

    dis = disassembler.Disassembler8080(motherboard.memory)
    deb = debugger.Debugger8080(motherboard, dis)

    if debug_mode:
        run, i, j = deb.debug(num_states, num_instructions)
        num_states += i
        num_instructions += j

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run, i, j = deb.debug(num_states, num_instructions)  # returns False if quit, true if not
                    num_states += i
                    num_instructions += j
                elif event.key == pygame.K_0:
                    motherboard.credit_pressed = True
                elif event.key == pygame.K_1:
                    motherboard.one_player_start_pressed = True
                elif event.key == pygame.K_2:
                    motherboard.two_player_start_pressed = True
                elif event.key == pygame.K_LEFT:
                    motherboard.player_one_left_pressed = True
                    motherboard.player_two_left_pressed = True
                elif event.key == pygame.K_RIGHT:
                    motherboard.player_one_right_pressed = True
                    motherboard.player_two_right_pressed = True
                elif event.key == pygame.K_SPACE:
                    motherboard.player_one_fire_pressed = True
                    motherboard.player_two_fire_pressed = True

        # Each state marks a clock period.  2MHz = 2 million clock periods per second.  60Hz refresh means 33,333
        # states before a redraw.  The two interrupts occur approx halfway through the period and then right before
        # the redraw.
        cur_states = 0
        while cur_states <= 16667 and run:
            try:
                i = motherboard.cpu.cycle()
                cur_states += i
                num_states += i
                num_instructions += 1
            except:
                deb.debug(num_states, num_instructions)
                run = False

        # first interrupt
        try:
            # Call will be RST 1
            i = motherboard.cpu.do_interrupt(1)
            cur_states += i
            num_states += i
        except:
            deb.debug(num_states, num_instructions)
            run = False


        while cur_states <= 33333 and run:
            try:
                i = motherboard.cpu.cycle()
            except:
                deb.debug(num_states, num_instructions)
                run = False
            cur_states += i
            num_states += i
            num_instructions += 1

        try:
            # Call will be RST 2
            i = motherboard.cpu.do_interrupt(2)
            cur_states += i
            num_states += i
        except:
            deb.debug(num_states, num_instructions)
            run = False


        motherboard.video_card.draw()

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("Start: {}".format(start_time))
    print("End: {}".format(end_time))
    print("Duration: {} sec.".format(duration))
    print("Num instructions: {}".format(num_instructions))
    print("Performance: {} cycles per second".format(num_states / duration))


    pygame.quit()


if __name__ == "__main__":
    # call the main function
    main()

