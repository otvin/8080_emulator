import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import datetime
import disassembler
import debugger
import motherboard

def main():
    debug_mode = False
    pygame.init()
    mb = motherboard.SpaceInvadersMotherBoard()

    if len(sys.argv) >= 2:
        if sys.argv[1].lower() in ['-?', '-h', '-help']:
            print('Usage: python3 space_invaders.py [options]')
            print('Options include:')
            print('-h, -help, -?  = this list')
            print('-debug = start in the debugger')
            print('-soundtest = test sounds, then exit\n')
            sys.exit()
        elif sys.argv[1].lower() == '-debug':
            debug_mode = True
        elif sys.argv[1].lower() == '-soundtest':
            mb.debug_sound_test()
            sys.exit()
        else:
            print('Invalid option: {}'.format(sys.argv[1]))
            print('try "python3 space_invaders.py -?" for help\n')
            sys.exit()

    run = True

    start_time = datetime.datetime.now()
    num_states = 0
    num_instructions = 0

    dis = disassembler.Disassembler8080(mb.memory)
    deb = debugger.Debugger8080(mb, dis)

    if debug_mode:
        run, i, j = deb.debug(num_states, num_instructions)
        num_states += i
        num_instructions += j

    loops = 0

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
                    mb.credit_pressed = True
                elif event.key == pygame.K_1:
                    mb.one_player_start_pressed = True
                elif event.key == pygame.K_2:
                    mb.two_player_start_pressed = True
                elif event.key == pygame.K_LEFT:
                    mb.player_one_left_pressed = True
                    mb.player_two_left_pressed = True
                elif event.key == pygame.K_RIGHT:
                    mb.player_one_right_pressed = True
                    mb.player_two_right_pressed = True
                elif event.key == pygame.K_SPACE:
                    mb.player_one_fire_pressed = True
                    mb.player_two_fire_pressed = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_0:
                    mb.credit_pressed = False
                elif event.key == pygame.K_1:
                    mb.one_player_start_pressed = False
                elif event.key == pygame.K_2:
                    mb.two_player_start_pressed = False
                elif event.key == pygame.K_LEFT:
                    mb.player_one_left_pressed = False
                    mb.player_two_left_pressed = False
                elif event.key == pygame.K_RIGHT:
                    mb.player_one_right_pressed = False
                    mb.player_two_right_pressed = False
                elif event.key == pygame.K_SPACE:
                    mb.player_one_fire_pressed = False
                    mb.player_two_fire_pressed = False

        # Each state marks a clock period.  2MHz = 2 million clock periods per second.  60Hz refresh means 33,333
        # states before a redraw.  The two interrupts occur approx halfway through the period and then right before
        # the redraw.
        cur_states = 0

        while cur_states <= 16667 and run:
            try:
                i = mb.cpu.cycle()
                cur_states += i
                num_states += i
                num_instructions += 1
            except (Exception, ):
                deb.debug(num_states, num_instructions)
                run = False
        
        # first interrupt
        if run:
            try:
                # Call will be RST 1
                i = mb.cpu.do_interrupt(1)
                cur_states += i
                num_states += i
                num_instructions += 1
            except (Exception, ):
                deb.debug(num_states, num_instructions)
                run = False

        while cur_states <= 33333 and run:
            try:
                i = mb.cpu.cycle()
                cur_states += i
                num_states += i
                num_instructions += 1
            except (Exception, ):
                deb.debug(num_states, num_instructions)
                run = False

        if run:
            try:
                # Call will be RST 2
                i = mb.cpu.do_interrupt(2)
                cur_states += i
                num_states += i
                num_instructions += 1
            except (Exception, ):
                deb.debug(num_states, num_instructions)
                run = False

        loops += 1
        if loops % 2 == 0:
            # pygame drawing is so slow... so if I draw it at 30Hz instead of 60Hz I get close to 2MHz on the CPU
            # performance.
            mb.video_card.draw()

        # NOTE - on faster hardware, a delay should be inserted here so that if it is running faster than 2MHz, we
        # slow things down.  Since it's right at 2MHz on my laptop, I'm not going to code it.

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("Start: {}".format(start_time))
    print("End: {}".format(end_time))
    print("Duration: {} sec.".format(duration))
    print("Num instructions: {}".format(num_instructions))
    print("Performance: {} states per second".format(num_states / duration))

    pygame.quit()


if __name__ == "__main__":
    # call the main function
    main()

