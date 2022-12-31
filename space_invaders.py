import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import datetime
import disassembler
import debugger
import memory
import videocard
import cpu


class SpaceInvadersMotherBoard:
    def __init__(self):
        self.memory = memory.SpaceInvadersMemory()
        self.video_card = videocard.SpaceInvadersScreen(self)
        self.cpu = cpu.I8080cpu(self)  # The CPU needs to access the motherboard to get to graphics, sound, and memory.
        self.stack_pointer_start = 0x2400  # needed for debugger to display the stack.  The SP itself gets set in code.


def main():

    debug_mode = False
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() in ['-?', '-h', '-help']:
            print('Usage: python3 space_invaders [options]')
            print('Options include:')
            print('-h, -help, -?  = this list')
            print('-debug = start in the debugger\n')
            sys.exit()
        elif sys.argv[1].lower() == '-debug':
            debug_mode = True
        else:
            print('Invalid option: {}'.format(sys.argv[1]))
            print('try "python3 space_invaders -?" for help\n')
            sys.exit()

    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()
    motherboard = SpaceInvadersMotherBoard()

    run = True

    start_time = datetime.datetime.now()
    num_cycles = 0
    last_instruction_time = datetime.datetime.now()

    dis = disassembler.Disassembler8080(motherboard.memory)
    deb = debugger.Debugger8080(motherboard, dis)

    if debug_mode:
        run, i = deb.debug()
        num_cycles += i

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = deb.debug()  # returns False if quit, true if not
        num_cycles += motherboard.cpu.cycle()

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("Start: {}".format(start_time))
    print("End: {}".format(end_time))
    print("Duration: {} sec.".format(duration))
    print("Performance: {} cycles per second".format(num_cycles / duration))

    pygame.quit()


if __name__ == "__main__":
    # call the main function
    main()

