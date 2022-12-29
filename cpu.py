class InvalidOpCodeException(Exception):
    pass


class OpcodeNotImplementedException(Exception):
    pass


class I8080cpu:

    def __init__(self, motherboard):

        self.motherboard = motherboard

        # program counter
        self.pc = 0x0

        # stack pointer
        self.sp = 0x0

        # 8-bit registers
        self.b = 0x0
        self.c = 0x0
        self.d = 0x0
        self.e = 0x0
        self.h = 0x0
        self.l = 0x0

        # 8-bit accumulator
        self.a = 0x0
        # 8-bit temporary accumulator (likely not needed as we can use local python variable)
        self.act = 0x0
        # 8-bit temporary register (likely not needed as we can use local python variable)
        self.tmp = 0x0

        # 5-bit flag register
        # zero, carry, sign, parity, auxiliary carry
        self.flags = 0x0

        # Using a list of functions to speed the lookup, vs. doing a big nested
        # if/else.
        self.operation_list = [
            None
        ]

    def debug_dump(self):
        ret_str = ""
        ret_str += "PC: 0x{}\n".format(hex(self.pc).upper()[2:])
        ret_str += "A: 0x{}\n".format(hex(self.a).upper()[2:])
        ret_str += "Flags: 0x{}\n".format(hex(self.flags).upper()[2:])
        ret_str += "SP: 0x{}\n".format(hex(self.sp).upper()[2:])
        ret_str += "B: 0x{}".format(hex(self.b)[2:].zfill(2).upper())
        ret_str += "C: 0x{}\n".format(hex(self.c)[2:].zfill(2).upper())
        ret_str += "D: 0x{}".format(hex(self.d)[2:].zfill(2).upper())
        ret_str += "E: 0x{}\n".format(hex(self.e)[2:].zfill(2).upper())
        ret_str += "H: 0x{}".format(hex(self.h)[2:].zfill(2).upper())
        ret_str += "L: 0x{}\n".format(hex(self.l)[2:].zfill(2).upper())
        return ret_str

    def fetch(self):
        pass

    def cycle(self):
        pass
