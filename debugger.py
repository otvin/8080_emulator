class Debugger8080:
    def __init__(self, motherboard, disassembler):
        self.motherboard = motherboard
        self.disassembler = disassembler

    def display_help(self):
        print("Debugger commands")
        print("     ?       Display this list")
        print("     s       Execute next line")
        print("     <enter> Execute next line")
        print("     s N     Execute next N lines, but will stop at a breakpoint")
        print("     b       Puts a breakpoint at the current line")
        print("     b 0xN   Puts a breakpoint at address N")
        print("     d 0xN   Deletes breakpoint at address N")
        print("     info b  list breakpoints")
        print("     bt      Prints the current stack")
        print("     r       Run program until next breakpoint [NOT IMPLEMENTED]")
        print("     rr      Exit debugger and return to normal execution [NOT IMPLEMENTED")
        print("     q       Terminate program and debugger")
        print("     int N   Send interrupt N to the system [NOT IMPLEMENTED]")
        print("     x 0xN   display contents of memory address N")

    def debug(self):

        breakpoint_list = []
        max_mem = self.motherboard.memory.max_mem()
        running = True
        continue_on_return = True  # do we keep running when we exit the debugger
        while running:
            print(self.motherboard.cpu.debug_dump())
            print("\n")
            print("Current +/- 10 bytes of instructions:")
            start = max(0, self.motherboard.cpu.pc - 10)
            end = min([self.motherboard.cpu.pc + 10, max_mem])
            print(self.disassembler.disassemble(start, end, self.motherboard.cpu.pc, breakpoint_list))
            print("\n")

            next_cmd = input("> ").lower()
            if len(next_cmd) == 0 or next_cmd[0] == "s":
                x = next_cmd.split()
                num_cycles = 1
                if len(x) > 1:
                    try:
                        num_cycles = int(x[1])
                    except:
                        print('invalid input {}'.format(x[1]))
                for i in range(num_cycles):
                    self.motherboard.cpu.cycle()
                    if self.motherboard.cpu.pc in breakpoint_list:
                        break
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
            elif next_cmd[0] == "d":
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
            elif next_cmd[0] == "x":
                x = next_cmd.split()
                if len(x) == 1:
                    print("Invalid input - need memory address to examine")
                else:
                    try:
                        mem_loc = int(x[1], 16)
                        print('Value of {} is 0x{}'.format(x[1],
                                                           hex(self.motherboard.memory[mem_loc])[2:].zfill(2).upper()))
                    except:
                        print("invalid input: {}".format(x[1]))
            elif next_cmd[0] == "q":
                running = False
                continue_on_return = False
            else:
                print("Invalid command.")

        return continue_on_return
