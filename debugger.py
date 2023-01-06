import traceback

class Debugger8080:
    def __init__(self, motherboard, disassembler):
        self.motherboard = motherboard
        self.disassembler = disassembler

    def display_help(self):
        print("Debugger commands")
        print("     ?           Display this list")
        print("     s           Execute next line")
        print("     <enter>     Execute next line")
        print("     s N         Execute next N lines, but will stop at a breakpoint")
        print("     b           Puts a breakpoint at the current line")
        print("     b 0xM       Puts a breakpoint at address M")
        print("     d 0xM       Deletes breakpoint at address M")
        print("     info b      list breakpoints")
        print("     bt          Prints the current stack")
        print("     r           Run program until next breakpoint")
        print("     rr          Exit debugger and return to normal execution")
        print("     q           Terminate program and debugger")
        print("     int N       Send interrupt N to the system")
        print("     x 0xM       display contents of memory address M")
        print("     x 0xM N     display contents of N bytes of memory starting with address M")
        print("     set 0xM 0xN set contents of memory address M with value N")
        print("     draw        tell video card to render the current screen")

    def debug(self, total_states=0, total_instructions=0):

        breakpoint_list = []
        max_mem = self.motherboard.memory.max_mem()
        running = True
        continue_on_return = True  # do we keep running when we exit the debugger
        while running:
            print(self.motherboard.cpu.debug_dump())
            print("\n")
            print("Instructions: {}\tStates:{}\n".format(total_instructions, total_states))
            print("Current +/- 10 bytes of instructions:")
            start = max(0, self.motherboard.cpu.pc - 10)
            end = min([self.motherboard.cpu.pc + 10, max_mem])
            print(self.disassembler.disassemble(start, end, self.motherboard.cpu.pc, breakpoint_list))
            print("\n")

            next_cmd = input("> ").lower()
            if len(next_cmd) == 0 or (next_cmd[0] == "s" and next_cmd[0:3] != "set"):
                x = next_cmd.split()
                num_states = 1
                if len(x) > 1:
                    try:
                        if x[1][0:2] == '0x':
                            num_states = int(x[1], 16)
                        else:
                            num_states = int(x[1])
                    except:
                        print('invalid input {}'.format(x[1]))
                for i in range(num_states):
                    try:
                        total_states += self.motherboard.cpu.cycle()
                    except:
                        traceback.print_exc()
                    else:
                        total_instructions += 1
                    if self.motherboard.cpu.pc in breakpoint_list:
                        break
            elif next_cmd[0:3] == "int":
                x = next_cmd.split()
                try:
                    which_int = int(x[1])
                    assert 0 <= which_int <= 7
                    total_states += self.motherboard.cpu.do_interrupt(which_int)
                except:
                    traceback.print_exc()
                else:
                    total_instructions += 1
            elif next_cmd == "r":
                t = True
                while t:
                    if self.motherboard.cpu.pc in breakpoint_list:
                        t = False
                    else:
                        try:
                            total_states += self.motherboard.cpu.cycle()
                        except:
                            traceback.print_exc()
                            t = False
                        else:
                            total_instructions += 1
            elif next_cmd == "rr":
                break
            elif next_cmd[0:3] == "set":
                x = next_cmd.split()
                try:
                    mem_addr = int(x[1], 16)
                    val = int(x[2], 16)
                    # using direct access to the memory array so that this command can overwrite ROM
                    self.motherboard.memory.memory[mem_addr] = val
                except:
                    print("invalid input {}".format(next_cmd))
            elif next_cmd[0] == "?":
                self.display_help()
            elif next_cmd == "bt":
                if self.motherboard.cpu.sp == self.motherboard.stack_pointer_start:
                    print("Stack empty")
                else:
                    print("Stack Addr & Value")
                    print("------------------")
                    for i in range(self.motherboard.cpu.sp, self.motherboard.stack_pointer_start, 2):
                        print('0x{}\t0x{}{}'.format(hex(i)[2:].zfill(4).upper(),
                                                    hex(self.motherboard.memory[i + 1])[2:].zfill(2).upper(),
                                                    hex(self.motherboard.memory[i])[2:].zfill(2).upper()))
            elif next_cmd[0] == "b":
                x = next_cmd.split()
                if len(x) > 1:
                    try:
                        bp = int(x[1], 16)
                        if bp not in breakpoint_list:
                            breakpoint_list.append(bp)
                    except:
                        print('Invalid input: {}'.format(x[1]))
                else:
                    breakpoint_list.append(self.motherboard.cpu.pc)
            elif next_cmd == "info b":
                if len(breakpoint_list) == 0:
                    print("No breakpoints set.")
                else:
                    print("Breakpoint list")
                    print("---------------")
                    for bp in breakpoint_list:
                        print('0x{}'.format(hex(bp)[2:].zfill(4).upper()))
                    print('\n')
            elif next_cmd == "d":
                x = next_cmd.split()
                if len(x) == 1:
                    print('Invalid input - need breakpoint to delete')
                else:
                    try:
                        bp = int(x[1], 16)
                        if bp not in breakpoint_list:
                            print("No breakpoint set at {}".format(x[1]))
                        else:
                            breakpoint_list.remove(bp)
                    except:
                        print("invalid input: {}".format(x[1]))
            elif next_cmd == "draw":
                self.motherboard.video_card.draw()
            elif next_cmd[0] == "x":
                x = next_cmd.split()
                if len(x) == 1:
                    print("Invalid input - need memory address to examine")
                else:
                    try:
                        if len(x) == 3:
                            if x[2][0:2].lower() == "0x":
                                num_addresses = int(x[2], 16)
                            else:
                                num_addresses = int(x[2], 10)
                        else:
                            num_addresses = 1
                        addr = int(x[1], 16)
                        for i in range(num_addresses):
                            print("{}: 0x{}".format(hex(addr)[2:].zfill(4).upper(),
                                                    hex(self.motherboard.memory[addr])[2:].zfill(2).upper()))
                            addr += 1
                        print('\n')
                    except:
                        print("invalid input: {}".format(next_cmd))
            elif next_cmd[0] == "q":
                running = False
                continue_on_return = False
            else:
                print("Invalid command.")

        return continue_on_return, total_states, total_instructions
