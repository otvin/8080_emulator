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
        self.stack_pointer_start = 0x23FF  # needed for debugger to display the stack
        self.cpu.sp = self.stack_pointer_start


def main():

    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()
    motherboard = SpaceInvadersMotherBoard()

    run = True

    start_time = datetime.datetime.now()
    num_instr = 0
    last_instruction_time = datetime.datetime.now()

    dis = disassembler.Disassembler8080(motherboard.memory)
    deb = debugger.Debugger8080(motherboard, dis)

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = deb.debug()  # returns False if quit, true if not

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("Start: {}".format(start_time))
    print("End: {}".format(end_time))
    print("Duration: {} sec.".format(duration))
    print("Performance: {} instructions per second".format(num_instr / duration))

    pygame.quit()


if __name__ == "__main__":
    # call the main function
    main()

