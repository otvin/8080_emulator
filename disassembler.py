ddd_sss_translation = ["B", "C", "D", "E", "H", "L", None, "A"]
ccc_translation = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]
rp_translation = ["BC", "DE", "HL", "SP"]


class InvalidOpcodeException(Exception):
    pass


def hexy(i, my_zfill=1, include_0x = False):
    # like hex() but my way
    if include_0x:
        mystr = "0x{}"
    else:
        mystr = "{}"
    return mystr.format(hex(i)[2:].zfill(my_zfill).upper())


def get_opcode_display(memory, location, num_bytes):
    assert 1 <= num_bytes <= 3
    a = hexy(memory[location], 2)
    if num_bytes >= 2:
        b = hexy(memory[location + 1], 2)
        if num_bytes == 3:
            c = hexy(memory[location + 2], 2)
        else:
            c = "  "
    else:
        b = "  "
        c = "  "
    return "{} {} {} ".format(a, b, c)

class Disassembler8080:
    def __init__(self, memory):
        self.memory = memory
        self.opcode_lookup = [self._NOP, self._LXI, self._STAX, self._INX, self._INR, self._DCR, self._MVI,
                              self._RLC, self.InvalidOpCode, self._DAD, self._LDAX, self._DCX, self._INR, self._DCR,
                              self._MVI, self._RRC,

                              self.InvalidOpCode, self._LXI, self._STAX, self._INX, self._INR, self._DCR, self._MVI,
                              self._RAL, self.InvalidOpCode, self._DAD, self._LDAX, self._DCX, self._INR, self._DCR,
                              self._MVI, self._RAR,

                              self.InvalidOpCode, self._LXI, self._SHLD, self._INX, self._INR, self._DCR, self._MVI,
                              self._DAA, self.InvalidOpCode, self._DAD, self._LHLD, self._DCX, self._INR, self._DCR,
                              self._MVI, self._CMA,

                              self.InvalidOpCode, self._LXI, self._STA, self._INX, self._INR, self._DCR, self._MVI,
                              self._STC, self.InvalidOpCode, self._DAD, self._LDA, self._DCX, self._INR, self._DCR,
                              self._MVI, self._CMC,

                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,
                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,

                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,
                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,

                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,
                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,

                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._HLT, self._MOV,
                              self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV, self._MOV,

                              self._ADD, self._ADD, self._ADD, self._ADD, self._ADD, self._ADD, self._ADD, self._ADD,
                              self._ADC, self._ADC, self._ADC, self._ADC, self._ADC, self._ADC, self._ADC, self._ADC,

                              self._SUB, self._SUB, self._SUB, self._SUB, self._SUB, self._SUB, self._SUB, self._SUB,
                              self._SBB, self._SBB, self._SBB, self._SBB, self._SBB, self._SBB, self._SBB, self._SBB,

                              self._ANA, self._ANA, self._ANA, self._ANA, self._ANA, self._ANA, self._ANA, self._ANA,
                              self._XRA, self._XRA, self._XRA, self._XRA, self._XRA, self._XRA, self._XRA, self._XRA,

                              self._ORA, self._ORA, self._ORA, self._ORA, self._ORA, self._ORA, self._ORA, self._ORA,
                              self._CMP, self._CMP, self._CMP, self._CMP, self._CMP, self._CMP, self._CMP, self._CMP,

                              self._RET, self._POP, self._JMP, self._JMP, self._CALL, self._PUSH, self._ADI, self._RST,
                              self._RET, self._RET, self._JMP, self.InvalidOpCode, self._CALL, self._CALL, self._ACI,
                              self._RST,

                              self._RET, self._POP, self._JMP, self._OUT, self._CALL, self._PUSH, self._SUI, self._RST,
                              self._RET, self.InvalidOpCode, self._JMP, self._IN, self._CALL, self.InvalidOpCode,
                              self._SBI, self._RST,

                              self._RET, self._POP, self._JMP, self._XTHL, self._CALL, self._PUSH, self._ANI, self._RST,
                              self._RET, self._PCHL, self._JMP, self._XCHG, self._CALL, self.InvalidOpCode, self._XRI,
                              self._RST,

                              self._RET, self._POP, self._JMP, self._DI, self._CALL, self._PUSH, self._ORI, self._RST,
                              self._RET, self._SPHL, self._JMP, self._EI, self._CALL, self.InvalidOpCode, self._CPI,
                              self._RST
                              ]


    def disassemble_space_invaders(self):
        # These are the ranges that are code, not data, according to
        # https://www.computerarcheology.com/Arcade/SpaceInvaders/Code.html
        print(self.disassemble(0x0, 0x0BF4))
        print(self.disassemble(0x1000, 0x13FD))
        print(self.disassemble(0x1400, 0x19BB))
        print(self.disassemble(0x19D1, 0x1A10))
        print(self.disassemble(0x1A32, 0x1A90))


    '''
    NOTE: The disassembly of many instructions shows a mnemonic followed by a second mnemonic in a comment.  E.G.
    in _MOV you see 
            "LD {}, {}\t; MOV r1, r2"
    Reason is that the other dissassemblies of ROMs and such use the former notation, but the latter matches the 
    i8080 instructions themselves. So, I could compare to other sites, while still knowing where to look in my code
    since my code lines up with the instruction names in the i8080 manuals.
    '''

    # DATA TRANSFER GROUP #

    def _MOV(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        sss = opcode & 0x7
        ret_str = ""
        if ddd != 0x06 and sss != 0x06:
            ret_str += "LD {}, {}\t; MOV r1, r2".format(ddd_sss_translation[ddd], ddd_sss_translation[sss])
            cycles = 1
            states = 5
        elif ddd != 0x06 and sss == 0x06:
            ret_str += "LD {}, (HL)\t; MOV r, M".format(ddd_sss_translation[ddd])
            cycles = 2
            states = 7
        else:  # ddd == 0x06 and sss != 0x06:
            ret_str += "LD (HL), {}\t; MOV M, r".format(ddd_sss_translation[sss])
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _MVI(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        ret_str = ""
        if ddd != 0x6:
            ret_str += "LD {}, ${}\t;MVI r, data".format(ddd_sss_translation[ddd], hexy(self.memory[cur_addr + 1], 2))
            cycles = 2
            states = 7
        else:
            ret_str += "LD (HL), ${}\t;MVI M, data".format(hexy(self.memory[cur_addr + 1], 2))
            cycles = 3
            states = 10
        return ret_str, 2, cycles, states

    def _LXI(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        ret_str = "LD {}, ${}{}\t;LXI rp, data 16".format(rp_translation[rp],
                                                          hexy(self.memory[cur_addr + 2], 2),
                                                          hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 3, 10

    def _LDA(self, opcode, cur_addr):
        ret_str = "LD A, (${}{})\t; LDA".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 4, 13

    def _STA(self, opcode, cur_addr):
        ret_str = "LD (${}{}), A\t; STA".format(hexy(self.memory[cur_addr + 2], 2),
                                                hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 4, 13

    def _LHLD(self, opcode, cur_addr):
        ret_str = "LD HL, (${}{})\t; LHLD".format(hexy(self.memory[cur_addr + 2], 2),
                                                  hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 5, 16

    def _SHLD(self, opcode, cur_addr):
        ret_str = "LD (${}{}), HL\t; SHLD".format(hexy(self.memory[cur_addr + 2], 2),
                                                  hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 5, 16

    def _LDAX(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        ret_str = "LDAX ({})".format(rp_translation[rp])
        return ret_str, 1, 2, 7

    def _STAX(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        ret_str = "STAX ({})".format(rp_translation[rp])
        return ret_str, 1, 2, 7

    def _XCHG(self, opcode, cur_addr):
        return "EX DE,HL\t; XCHG", 1, 1, 4

    # ARITHMETIC GROUP #

    def _ADD(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "ADD A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "ADD A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ADI(self, opcode, cur_addr):
        ret_str = "ADD A, ${}\t; ADI data".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _ADC(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "ADC A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "ADC A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ACI(self, opcode, cur_addr):
        ret_str = "ACI A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _SUB(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "SUB A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "SUB A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _SUI(self, opcode, cur_addr):
        ret_str = "SUB A, ${}\t; SUI data".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _SBB(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "SBB A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "SBB A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _SBI(self, opcode, cur_addr):
        ret_str = "SBI A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _INR(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            ret_str = "INC {}\t; INR r".format(ddd_sss_translation[ddd])
            cycles = 1
            states = 5
        else:
            ret_str = "INC (HL)\t; INR M"
            cycles = 3
            states = 10
        return ret_str, 1, cycles, states

    def _DCR(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            ret_str = "DEC {}\t; DCR r".format(ddd_sss_translation[ddd])
            cycles = 1
            states = 5
        else:
            ret_str = "DEC (HL)\t; DCR M"
            cycles = 3
            states = 10
        return ret_str, 1, cycles, states

    def _INX(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        ret_str = "INC {}\t; INX rp".format(rp_translation[rp])
        return ret_str, 1, 1, 5

    def _DCX(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        ret_str = "DEC {}\t; DCX rp".format(rp_translation[rp])
        return ret_str, 1, 1, 5

    def _DAD(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        ret_str = "ADD HL,{}\t; DAD rp".format(rp_translation[rp])
        return ret_str, 1, 3, 10

    def _DAA(self, opcode, cur_addr):
        return "DAA", 1, 1, 4

    # LOGICAL GROUP

    def _ANA(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "AND {}\t; ANA r".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "AND (HL)\t; ANA M"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ANI(self, opcode, cur_addr):
        ret_str = "AND ${}\t; ANI data".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _XRA(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "XOR {}\t; XRA r".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "XOR (HL)\t; XRA M"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _XRI(self, opcode, cur_addr):
        ret_str = "XOR ${}\t; XRI data".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _ORA(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "OR {}\t; ORA r".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "OR (HL)\t; ORA M"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ORI(self, opcode, cur_addr):
        ret_str = "OR ${}\t; ORI data".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _CMP(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            ret_str = "CMP {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            ret_str = "CMP (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _CPI(self, opcode, cur_addr):
        ret_str = "CMP ${}\t; CPI data".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _RLC(self, opcode, cur_addr):
        return "RLC", 1, 1, 4

    def _RRC(self, opcode, cur_addr):
        return "RRCA", 1, 1, 4

    def _RAL(self, opcode, cur_addr):
        return "RAL", 1, 1, 4

    def _RAR(self, opcode, cur_addr):
        return "RAR", 1, 1, 4

    def _CMA(self, opcode, cur_addr):
        return "CMA", 1, 1, 4

    def _CMC(self, opcode, cur_addr):
        return "CMC", 1, 1, 4

    def _STC(self, opcode, cur_addr):
        return "STC", 1, 1, 4

    # BRANCH GROUP

    def _JMP(self, opcode, cur_addr):
        if opcode == 0xC3:
            ret_str = "JMP ${}{}".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        else:
            ccc = (opcode >> 3) & 0x7
            ret_str = "JMP {} ${}{}".format(ccc_translation[ccc],
                                            hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 3, 10

    def _CALL(self, opcode, cur_addr):
        if opcode == 0xCD:
            ret_str = "CALL ${}{}".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        else:
            ccc = (opcode >> 3) & 0x7
            ret_str = "CALL {} ${}{}".format(ccc_translation[ccc],
                                             hexy(self.memory[cur_addr + 2], 2),
                                             hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 5, 17  # cycles/states not accurate if CALL condition = false

    def _RET(self, opcode, cur_addr):
        if opcode == 0xC9:
            ret_str = "RET"
            cycles = 3
            states = 10
        else:
            ccc = (opcode >> 3) & 0x7
            ret_str = "RET {}".format(ccc_translation[ccc])
            cycles = 3
            states = 11
        return ret_str, 1, cycles, states  # cycles/states not accurate if RET condition = false

    def _RST(self, opcode, cur_addr):
        nnn = (opcode >> 3) & 0x7
        ret_str = "RST {}".format(hexy(nnn, 3))
        return ret_str, 1, 3, 11

    def _PCHL(self, opcode, cur_addr):
        return "PCHL", 1, 1, 5

    # STACK, I/O, and MACHINE CONTROL GROUP

    def _PUSH(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        if rp != 0x3:
            ret_str = "PUSH {}".format(rp_translation[rp])
        else:
            ret_str = "PUSH AF"
        return ret_str, 1, 3, 11

    def _POP(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        if rp != 0x3:
            ret_str = "POP {}".format(rp_translation[rp])
        else:
            ret_str = "POP AF"
        return ret_str, 1, 3, 10

    def _XTHL(self, opcode, cur_addr):
        return "XTHL", 1, 5, 18

    def _SPHL(self, opcode, cur_addr):
        return "SPHL", 1, 1, 5

    def _IN(self, opcode, cur_addr):
        ret_str = "IN A, (INP {})".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 3, 10

    def _OUT(self, opcode, cur_addr):
        ret_str = "OUT (OUT ${}), A".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 3, 10

    def _EI(self, opcode, cur_addr):
        return "EI", 1, 1, 4

    def _DI(self, opcode, cur_addr):
        return "DI", 1, 1, 4

    def _HLT(self, opcode, cur_addr):
        return "HLT", 1, 1, 7

    def _NOP(self, opcode, cur_addr):
        return "NOP", 1, 1, 4

    def InvalidOpCode(self, opcode, cur_addr):
        raise InvalidOpcodeException("Invalid opcode: {}".format(opcode))

    def disassemble(self, start_addr, max_addr, point_addr=None, breakpoint_list=None):
        # point_addr = address which will receive a pointer next to it
        if breakpoint_list is None:
            breakpoint_list = []

        cur_addr = start_addr
        ret_str = ""
        while cur_addr <= max_addr:
            opcode = self.memory[cur_addr]
            # if we are looking at data, or if we are looking back 10 bytes and it doesn't land at a start of an
            # instruction, we can get an invalid opcode but it's not really an error.

            try:
                res = self.opcode_lookup[opcode](opcode, cur_addr)
                if point_addr is not None and cur_addr == point_addr:
                    ret_str += "--->\t"
                else:
                    ret_str += "\t"
                if cur_addr in breakpoint_list:
                    ret_str += '*'
                ret_str += "{}: ".format(hexy(cur_addr, 4))
                ret_str += get_opcode_display(self.memory, cur_addr, res[1]) + res[0] + '\n'
                cur_addr += res[1]
            except InvalidOpcodeException:
                ret_str += "\t{}: ".format(hexy(cur_addr, 4))
                ret_str += get_opcode_display(self.memory, cur_addr, 1) + '??' + '\n'
                cur_addr += 1

        return ret_str
