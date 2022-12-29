class Debugger8080:
    def __init__(self, motherboard, disassembler):
        self.motherboard = motherboard
        self.disassembler = disassembler

    def display_help(self):
        print("Debugger commands")
        print("     ?       Display this list")
        print("     s       Execute next line")
        print("     s N     Execute next N lines, but will stop at a breakpoint")
        print("     b       Puts a breakpoint at the current line")
        print("     b N     Puts a breakpoint at line N")
        print("     d N     Deletes breakpoint at line N")
        print("     info b  list breakpoints")
        print("     bt      Prints the current stack")
        print("     r       Run program until next breakpoint")
        print("     q       Terminate program and debugger")

    def debug(self):

        breakpoint_list = []
        max_mem = self.motherboard.memory.max_mem()
        running = True
        continue_on_return = True  # do we keep running when we exit the debugger
        while running:
            print(self.motherboard.cpu.debug_dump())
            print("\n")
            print("Current + next 10 instructions:")
            start = self.motherboard.cpu.pc
            end = min([self.motherboard.cpu.pc + 10, max_mem])
            print(self.disassembler.disassemble(start, end))
            print("\n")

            next_cmd = input("> ")
            if next_cmd[0] == "?":
                self.display_help()
            elif next_cmd[0] == "q":
                running = False
                continue_on_return = False
            else:
                print("Invalid command.")

        return continue_on_return
