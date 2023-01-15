import sys
import datetime
import disassembler
import debugger
import motherboard

'''
    Virtual computer to run 8080 Emulator tests.  Tests may be found at https://altairclone.com/downloads/cpu_tests/
    
    The tests are designed to be run in a system emulating the CP/M operating system.  Per 
    https://retrocomputing.stackexchange.com/questions/9361/test-emulated-8080-cpu-without-an-os, we can use a quick
    shim that puts a HLT at 0x0000 in memory, and a simple "print" function at 0x0005.  I copied the work from
    https://github.com/gergoerdi/clash-intel8080/blob/master/test/Hardware/Intel8080/TestBench.hs to put the following
    source in memory starting 0x0000.  The test ROMs load at 0x0100.
'''

CPM_SHIM = [
    0x3e, 0x0a,        # 0x0000: exit:    MVI A, 0x0a
    0xd3, 0x00,        # 0x0002:          OUT 0
    0x76,              # 0x0004:          HLT

    0x3e, 0x02,        # 0x0005: message: MVI A, 0x02
    0xb9,              # 0x0007:          CMP C
    0xc2, 0x0f, 0x00,  # 0x0008:          JNZ 0x000f
    0x7b,              # 0x000B: putChr:  MOV A, E
    0xd3, 0x00,        # 0x000C:          OUT 0
    0xc9,              # 0x000E:          RET

    0x0e, 0x24,        # 0x000F: putStr:  MVI C, '$'
    0x1a,              # 0x0011: loop:    LDAX DE
    0xb9,              # 0x0012:          CMP C
    0xc2, 0x17, 0x00,  # 0x0013:          JNZ next
    0xc9,              # 0x0016:          RET
    0xd3, 0x00,        # 0x0017: next:    OUT 0
    0x13,              # 0x0019:          INX DE
    0xc3, 0x11, 0x00   # 0x001a:          JMP loop
]

def main():
    debug_mode = False
    which_test = ""
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() in ['-?', '-h', '-help']:
            print('Usage: python3 test8080_system.py [ROM name] [options]')
            print('or python3 test8080_sytem.py -? for this list')
            print('ROM name options:')
            print('TST8080 or 8080EXER')
            print('Options:')
            print('-debug = start in the debugger')
        elif sys.argv[1].lower() in['tst8080', '8080exm', '8080pre', 'cputest']:
            which_test = sys.argv[1].upper() + '.COM'
        else:
            print('Invalid ROM name.  Valid ROMs are TST8080, 8080PRE, CPUTEST, and 8080EXM')
            sys.exit()
        if len(sys.argv) >= 3:
            if sys.argv[2].lower() == '-debug':
                debug_mode = True
            else:
                print('Invalid option.  Only valid option is -debug')
    else:
            print('Invalid options.')
            print('try "python3 test8080_system.py -?" for help\n')
            sys.exit()

    mb = motherboard.Test8080SystemMotherBoard(which_test)
    mb.load_cpm_shim(CPM_SHIM)
    start_time = datetime.datetime.now()
    run = True
    num_states = 0
    num_instructions = 0
    dis = disassembler.Disassembler8080(mb.memory)
    deb = debugger.Debugger8080(mb, dis)
    if debug_mode:
        run, i, j = deb.debug(num_states, num_instructions)
        num_states += i
        num_instructions += j

    while run and not(mb.cpu.halted):
        try:
            i = mb.cpu.cycle()
            num_states += i
            num_instructions += 1
        except (Exception, ):
            deb.debug(num_states, num_instructions)
            run = False

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("Start: {}".format(start_time))
    print("End: {}".format(end_time))
    print("Duration: {} sec.".format(duration))
    print("Num instructions: {}".format(num_instructions))
    print("Performance: {} states per second".format(num_states / duration))

if __name__ == "__main__":
    # call the main function
    main()