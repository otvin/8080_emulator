
ddd_sss_translation = ["B", "C", "D", "E", "H", "L", None, "A"]
ccc_translation = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]
rp_translation = ["BC", "DE", "HL", "SP"]


class DisassemblyNotImplementedException(Exception):
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


    # DATA TRANSFER GROUP #

    def _MOV(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        sss = opcode & 0x7
        ret_str = ""
        if ddd != 0x06 and sss != 0x06:
            # MOV r1, r2
            # Move Register
            # The content of register r2 is moved to register r1
            # 1 cycle, 5 states
            ret_str += "LD {}, {}".format(ddd_sss_translation[ddd], ddd_sss_translation[sss])
            cycles = 1
            states = 5
        elif ddd != 0x06 and sss == 0x06:
            # MOV r, M
            # Move from memory
            # The content of the memory location, whose address is in registers H and L is moved to register r
            # 2 cycles, 7 states
            ret_str += "LD {}, (HL)".format(ddd_sss_translation[ddd])
            cycles = 2
            states = 7
        else:  # ddd == 0x06 and sss != 0x06:
            # MOV M, r
            # Move to memory
            # The content of register r is moved to the memory location whose address is in registers H and L
            # 2 cycles, 7 states
            ret_str += "LD (HL), {}".format(ddd_sss_translation[sss])
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _MVI(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        ret_str = ""
        if ddd != 0x6:
            # MVI r, data
            # Move Immediate
            # The content of byte 2 of the instruction is moved to register r
            # 2 cycles, 7 states
            # The disassembled ROM at Computer Archaeology uses "LD" for Load instead of MVI.
            ret_str += "LD {}, ${}".format(ddd_sss_translation[ddd], hexy(self.memory[cur_addr + 1], 2))
            cycles = 2
            states = 7
        else:
            # MVI M, data
            # Move to memory immediate
            # The content of byte 2 of the instruction is moved to the memory location whose address is in
            # registers H and L
            # 3 cycles 10 states
            ret_str += "LD (HL), ${}".format(hexy(self.memory[cur_addr + 1], 2))
            cycles = 3
            states = 10
        return ret_str, 2, cycles, states

    def _LXI(self, opcode, cur_addr):
        # LXI rp, data 16
        # Load register pair immediate
        # Byte 3 of the instruction is moved into the high-order register (rh) of the register pair rp.
        # Byte 2 of the instruction is moved into the low-order register (rl) of the register pair rp.
        # 3 cycles 10 states
        rp = (opcode >> 4) & 0x3
        ret_str = "LD {}, ${}{}".format(rp_translation[rp],
                                        hexy(self.memory[cur_addr + 2], 2),
                                        hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 3, 10

    def _LDA(self, opcode, cur_addr):
        # LDA addr
        # Load accumulator direct
        # The content of the memory location, whose address is specified in byte 2 and byte 3 of the
        # instruction, is moved to register A.
        # 4 cycles 13 states
        ret_str = "LD A, (${}{})".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 4, 13

    def _STA(self, opcode, cur_addr):
        # STA addr
        # Store accumulator direct
        # The content of the accumulator is moved to the memory location whose address is specified in byte 2
        # and byte 3 of the instruction
        # 4 cycles 13 states
        ret_str = "LD (${}{}), A".format(hexy(self.memory[cur_addr + 2], 2),
                                         hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 4, 13

    def _LHLD(self, opcode, cur_addr):
        # LHLD addr
        # Load H and L direct
        # The content of the memory location, whose address is specified in byte 2 and byte 3 of the
        # instruction,is moved to register L.  The content of the memory location at the succeeding address is
        # moved to register H.
        # 5 cycles 16 states
        ret_str = "LD HL, (${}{})".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 5, 16

    def _SHLD(self, opcode, cur_addr):
        # SHLD addr
        # Store H and L direct
        # The content of register L is moved to the memory location whose address is specified in byte 2 and
        # byte 3.  The content of register H is moved to the succeeding memory location.
        # 5 cycles 16 states
        ret_str = "LD (${}{}), HL".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 5, 16

    def _LDAX(self, opcode, cur_addr):
        # LDAX rp
        # Load accumulator indirect
        # The content of the memory location, whose address is in the register pair rp, is moved to register
        # A.  Note only register pairs rp=B (registers B and C) or rp=D (registers D and E) may be specified.
        # 2 cycles 7 states
        rp = (opcode >> 4) & 0x3
        ret_str = "LDAX ({})".format(rp_translation[rp])
        return ret_str, 1, 2, 7

    def _STAX(self, opcode, cur_addr):
        # STAX rp
        # Store accumulator indirect
        # The content of register A is moved to teh memory location whose address is in the register pair rp.
        # Note: only register pairs rp=B (registers B and C) or rp=D (registers D and E) may be specified.
        # 2 cycles 7 states
        rp = (opcode >> 4) & 0x3
        ret_str = "STAX ({})".format(rp_translation[rp])
        return ret_str, 1, 2, 7

    def _XCHG(self, opcode, cur_addr):
        # XCHG
        # Exchange H and L with D and E
        # THe contents of registers H and L are exchanged with the contents of registers D and E
        # 1 cycle 4 states
        return "EX DE,HL", 1, 1, 4

    # ARITHMETIC GROUP #

    def _ADD(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # ADD r
            # Add register
            # The content of register r is added to the content of the accumulator.  The result is placed in the
            # accumulator.
            # 1 cycle 4 states
            ret_str = "ADD A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # ADD M
            # Add memory
            # The content of the memory location whose address is contained in the H and L registers is added
            # to the content of the accumulator.  The result is placed in the accumulator.
            # 2 cycles 7 states
            ret_str = "ADD A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ADI(self, opcode, cur_addr):
        # ADI data
        # Add Immediate
        # The contents of the second byte of the instruction is added to the content of the accumulator.  The
        # result is placed in the accumulator.
        # 2 cycles 7 states
        ret_str = "ADD A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _ADC(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # ADC r
            # Add register with carry
            # The content of register r and the content of the carry bit are added to the content of the
            # accumulator.  The result is placed in the accumulator.
            # 1 cycle 4 states
            ret_str = "ADC A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # ADC M
            # Add memory with carry
            # The content of the memory location whose address is contained in the H and L registers is added
            # and the content of the CY flag are added to the content of the accumulator.  The result is placed
            # in the accumulator.
            # 2 cycles 7 states
            ret_str = "ADC A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ACI(self, opcode, cur_addr):
        # ACI data
        # Add immediate with carry
        # The content of the second byte of the instruction and the content of the CY flag are added to the
        # contents of the accumulator.  THe result is placed in the accumulator.
        # 2 cycles 7 states
        ret_str = "ACI A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _SUB(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # SUB r
            # Subtract register
            # The content of register r is subtracted from the content of the accumulator.  The result is placed in
            # the accumulator.
            # 1 cycle 4 states
            ret_str = "SUB A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # SUB M
            # Subtract memory
            # The content of the memory location whose address is contained in the H and L registers is subtracted
            # from the content of the accumulator.  The result is placed in the accumulator.
            # 2 cycles 7 states
            ret_str = "SUB A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _SUI(self, opcode, cur_addr):
        # SUI data
        # Subtract Immediate
        # The content of the second byte of the instruction is subtracted from the content of the accumulator.
        # The result is placed in the accumulator.
        # 2 cycles 7 states
        ret_str = "SUB A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _SBB(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # SBB r
            # Subtract register with borrow
            # The content of register r and the content of the CY flag are both subtracted from the
            # accumulator.  The result is placed in the accumulator.
            # 1 cycle 4 states
            ret_str = "SBB A, {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # SBB M
            # Subtract memory with borrow
            # The content of the memory location whose address is contained in the H and L registers
            # and the content of the CY flag are both subtracted from the accumulator.  The result is placed
            # in the accumulator.
            # 2 cycles 7 states
            ret_str = "SBB A, (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _SBI(self, opcode, cur_addr):
        # SBI data
        # Subtract immediate with borrow
        # The content of the second byte of the instruction and the contents of the CY flag are both subtracted
        # from the accumulator.  The result is placed in the accumulator.
        # 2 cycles 7 states
        ret_str = "SBI A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _INR(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            # INR r
            # Increment Register
            # The content of register r is incremented by one.  Note: All condition flags except CY are affected.
            # 1 cycle 5 states
            ret_str = "INC {}".format(ddd_sss_translation[ddd])
            cycles = 1
            states = 5
        else:
            # INR M
            # Increment Memory
            # The content of the memory location whose address is contained in the H and L registers is incremented
            # by one.  Note: All condition flags except CY are affected.
            # 3 cycles 10 states
            ret_str = "INC (HL)"
            cycles = 3
            states = 10
        return ret_str, 1, cycles, states

    def _DCR(self, opcode, cur_addr):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            # DCR r
            # Decrement Register
            # The content of register r is decremented by one.  Note: All condition flags except CY are affected.
            # 1 cycle 5 states
            ret_str = "DEC {}".format(ddd_sss_translation[ddd])
            cycles = 1
            states = 5
        else:
            # DCR M
            # Decrement Memory
            # The content of the memory location whose address is contained in the H and L registers is decremented
            # by one.  Note: All condition flags except CY are affected.
            # 3 cycles 10 states
            ret_str = "DEC (HL)"
            cycles = 3
            states = 10
        return ret_str, 1, cycles, states

    def _INX(self, opcode, cur_addr):
        # INX rp
        # Increment register pair
        # The content of the register pair rp is incremented by one.  No condition flags are affected.
        # 1 cycle 5 states
        rp = (opcode >> 4) & 0x3
        ret_str = "INC {}".format(rp_translation[rp])
        return ret_str, 1, 1, 5

    def _DCX(self, opcode, cur_addr):
        # DCX rp
        # Decrement register pair
        # The content of the register pair rp is decremented by one.  No condition flags are affected.
        # 1 cycle 5 states
        rp = (opcode >> 4) & 0x3
        ret_str = "DEC {}".format(rp_translation[rp])
        return ret_str, 1, 1, 5

    def _DAD(self, opcode, cur_addr):
        # DAD rp
        # Add register pair to H and L
        # The content of the register pair rp is added to the register pair H and L.  THe result is placed in
        # the register pair H and L.  Note: Only the CY flag is affected.  If is set if there is a carry out
        # of the double precision add; otherwise it is reset.
        # 3 cycles 10 states
        rp = (opcode >> 4) & 0x3
        ret_str = "ADD HL,{}".format(rp_translation[rp])
        return ret_str, 1, 3, 10

    def _DAA(self, opcode, cur_addr):
        # DAA
        # Decimal Adjust Accumulator
        # The eight-bit number in the accumulator is adjusted to form two four-bit Binary-Coded-Decimal digits
        # by the following process:
        # 1. If the value of the least significant 4 bits of the accumulator is greater than 9 or if the AC flag
        # is set, 6 is added to the accumulator.
        # 2. If the value of the most significant 4 bits of the accumulator is now greater than 9, or if the CY
        # flag is set, 6 is added to the most significant 4 bits of the accumulator.
        # NOTE: All flags are affected
        # 1 cycle 4 states
        return "DAA", 1, 1, 4

    # LOGICAL GROUP

    def _ANA(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # ANA r
            # AND register
            # The content of register r is logically anded with teh content of the accumulator.  The result is
            # placed in the accumulator.  The CY flag is cleared.
            # 1 cycle 4 states
            ret_str = "AND {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # ANA M
            # AND memory
            # THe contents of the memory location whose address is contained in the H and L registers is logically
            # anded with the content of the accumulator.  The result is placed in the accumulator.  The CY flag is
            # cleared.
            # 2 cycles 7 states
            ret_str = "AND (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ANI(self, opcode, cur_addr):
        # ANI data
        # AND immediate
        # The content of the second byte of the instruction is logically anded with the contents of the
        # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
        # 2 cycles 7 states
        ret_str = "AND ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _XRA(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # XRA r
            # Exclusive OR register
            # The content of register r is logically exclusive-or'd with the content of the accumulator.  The result
            # is placed in the accumulator.  The CY and AC flags are cleared.
            # 1 cycle 4 states
            ret_str = "XOR {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # XRA M
            # Exclusive OR memory
            # THe contents of the memory location whose address is contained in the H and L registers is exclusive-
            # OR'd with the content of the accumulator.  The result is placed in the accumulator.  The AC and CY
            # flags are cleared.
            # 2 cycles 7 states
            ret_str = "XOR (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _XRI(self, opcode, cur_addr):
        # XRI data
        # Exclusive OR immediate
        # The content of the second byte of the instruction is exclusive-OR'd with the content of the
        # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
        # 2 cycles 7 states
        ret_str = "XOR ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _ORA(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # ORA r
            # OR register
            # The content of register r is logically inclusive-or'd with the content of the accumulator.  The result
            # is placed in the accumulator.  The CY and AC flags are cleared.
            # 1 cycle 4 states
            ret_str = "OR {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # ORA M
            # OR memory
            # THe contents of the memory location whose address is contained in the H and L registers is inclusive-
            # OR'd with the content of the accumulator.  The result is placed in the accumulator.  The AC and CY
            # flags are cleared.
            # 2 cycles 7 states
            ret_str = "OR (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _ORI(self, opcode, cur_addr):
        # ORI data
        # OR immediate
        # The content of the second byte of the instruction is inclusive-OR'd with the content of the
        # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
        # 2 cycles 7 states
        ret_str = "OR ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _CMP(self, opcode, cur_addr):
        sss = opcode & 0x7
        if sss != 0x6:
            # CMP r
            # Compare Register
            # The content of register r is subtracted from the accumulator.  THe accumulator remains unchanged.
            # The condition flags are set as a result of the subtraction.  The Z flag is set to 1 if (A) = (r).
            # The CY flag is set to 1 if (A) < (r)
            # 1 cycle 4 states
            ret_str = "CMP {}".format(ddd_sss_translation[sss])
            cycles = 1
            states = 4
        else:
            # CMP M
            # Compare memory
            # The content of the memory location whose address is contained in the H and L registers is subtracted
            # from the accumulator.  The accumulator remains unchanged.  The condition lfags are set as a result
            # of the subtraction.  The Z flag is set to 1 if (A) = ((H)(L)).  The CY flag is set to 1 if (A) <
            # ((H)(L)).
            # 2 cycles 7 states
            ret_str = "CMP (HL)"
            cycles = 2
            states = 7
        return ret_str, 1, cycles, states

    def _CPI(self, opcode, cur_addr):
        # CPI data
        # Compare immediate
        # THe content of teh second byte of the instruction is subtracted from the accumulator.  The condition
        # flags are set by the result of the subtraction.  The Z flag is set to 1 if (A) = (byte 2).  The CY
        # flag is set to 1 if (A) < (byte 2).
        # NOTE: My inference is that A is unchanged, even though this isn't stated.
        # 2 cycles 7 states
        ret_str = "CMP ${}".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 2, 7

    def _RLC(self, opcode, cur_addr):
        # RLC
        # Rotate left
        # The content of the accumulator is rotated left one position.  The low order bit and the CY flag are
        # both set to the value shifted out of the high order bit position.  Only the CY flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        return "RLC", 1, 1, 4

    def _RRC(self, opcode, cur_addr):
        # RRC
        # Rotate right
        # The content of the accumulator is rotated right one position.  The high order bit and the CY flag are
        # both set to the value shifted out of the low order bit position.  Only the CY flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        return "RRCA", 1, 1, 4

    def _RAL(self, opcode, cur_addr):
        # RAL
        # Rotate left through carry
        # The content of the accumulator is rotated left one position.  The low order bit is set equal to the
        # CY flag and the CY flag is set to the value shifted out of the high order bit position.  Only the CY
        # flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        return "RAL", 1, 1, 4

    def _RAR(self, opcode, cur_addr):
        # RAR
        # Rotate right through carry
        # The content of the accumulator is rotated right one position.  The high order bit and the CY flag is
        # set to the CY flag and the CY flag is set to the value shifted out of the low order bit position.
        # Only the CY flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        return "RAR", 1, 1, 4

    def _CMA(self, opcode, cur_addr):
        # CMA
        # Complement accumulator
        # The contents of the accumulator are complemented (zero bits become 1, one bits become 0).  No flags
        # are affected.
        # 1 cycle 4 states
        return "CMA", 1, 1, 4

    def _CMC(self, opcode, cur_addr):
        # CMC
        # The CY flag is complemented.  No other flags are affected.
        # 1 cycle 4 states
        return "CMC", 1, 1, 4

    def _STC(self, opcode, cur_addr):
        # STC
        # The CY flag is set to 1.  No other flags are affected.
        # 1 cycle 4 states
        return "STC", 1, 1, 4

    # BRANCH GROUP

    def _JMP(self, opcode, cur_addr):
        if opcode == 0xC3:
            # JMP addr
            # Control is transferred to the instruction whose address is specified in byte 3 and byte 2 of
            # the current instruction
            # 3 cycles 10 states
            ret_str = "JMP ${}{}".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        else:
            # JMP condition addr
            # If the specified condition is true, control is transferred to the instruction whose address is
            # specified in byte 3 and byte 2 of the current instruction; otherwise, control continues sequentially.
            # 3 cycles 10 states
            ccc = (opcode >> 3) & 0x7
            ret_str = "JMP {} ${}{}".format(ccc_translation[ccc],
                                            hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 3, 10

    def _CALL(self, opcode, cur_addr):
        if opcode == 0xCD:
            # CALL addr
            # The high-order 8 bits of the next instruction address are moved to the memory address that is one
            # less than the content of register SP.  The low order 8 bits of the next instruction address are moved
            # to the memory location whose address is two less than the content of register SP.  THe content of
            # register SP is decremented by 2.  Control is transferred to the instruction whose address is specified
            # in byte 3 and byte 2 of the current instruction.
            # So basically - (SP) gets PC + 3 / PC + 4, decrement SP, jump to the address specified in bytes 2 & 3
            # 5 cycles 17 states
            ret_str = "CALL ${}{}".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
        else:
            # CALL condition addr
            # If the specified condition is true, the actions specified in the CALL instruction (see above) are
            # performed; otherwise, control continues sequentially
            # If condition true:  5 cycles / 17 states
            # If condition false: 3 cycles / 11 states
            ccc = (opcode >> 3) & 0x7
            ret_str = "CALL {} ${}{}".format(ccc_translation[ccc],
                                             hexy(self.memory[cur_addr + 2], 2),
                                             hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 3, 5, 17  # cycles/states not accurate if CALL condition = false

    def _RET(self, opcode, cur_addr):
        if opcode == 0xC9:
            # RET
            # THe content of the memory location whose address is specified in register SP is moved to the low
            # order eight bits of register PC.  THe content of the memory location whose address is one more than
            # the content of register SP is moved to the high-order 8 bits of register PC.  THe content of register
            # SP is incremented by 2.
            # 3 cycles 10 states
            ret_str = "RET"
            cycles = 3
            states = 10
        else:
            # RET condition
            # If the specified condition is true, the actions specified in the RET instruction (see above) are
            # performed; otherwise, control continues sequentially.
            # If condition true: 3 cycles / 11 states
            # If condition false: 1 cycles / 5 states
            ccc = (opcode >> 3) & 0x7
            ret_str = "RET {}".format(ccc_translation[ccc])
            cycles = 3
            states = 11
        return ret_str, 1, cycles, states  # cycles/states not accurate if RET condition = false

    def _RST(self, opcode, cur_addr):
        # RST n
        # Restart
        # The high-order eight bits of the next instruction address are moved to the memory location whose
        # address is one less than the content of register SP.  THe low-order eight bits of the next instruction
        # address are moved to the memory location whose address is two less than the content of register SP.
        # THe content of register SP is decremented by two.  Control is transferred to teh instruction whose
        # address is 8 times the content of NNN.
        # Note the shortcut here is to set PC = 00 + (opcode & 0x56)
        # 3 cycles 11 states
        nnn = (opcode >> 3) & 0x7
        ret_str = "RST {}".format(hexy(nnn, 3))
        return ret_str, 1, 3, 11

    def _PCHL(self, opcode, cur_addr):
        # PCHL
        # Jump H and L indirect - move H and L to PC
        # The content of register H is moved to teh high-order eight bits of register PC.  The content of
        # register L is moved to the low-order eight bits of register PC
        # 1 cycle 5 states
        return "PCHL", 1, 1, 5

    # STACK, I/O, and MACHINE CONTROL GROUP

    def _PUSH(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        if rp != 0x3:
            # PUSH rp
            # The content of thh high-order register of register pair rp is moved to the memory location whose
            # address is one less than the content of register SP.  The content of the low-order register of
            # register pair rp is moved to the memory location whose address is two less than the content of
            # register SP.  The content of register SP is decremented by 2.  Note: Register pair rp = SP may
            # not be specified
            # 3 cycles 11 states
            ret_str = "PUSH {}".format(rp_translation[rp])
        else:
            # PUSH PSW
            # Push processor status word
            # Note - rp == 0x3 is same as rp_translation[rp] == "SP", but we're not actually pushing SP
            # The content of register A is moved to the memory location whose address is one less than register SP.
            # The contents of the condition flags are assembled into a processor status word and the word is moved
            # to the memory location whose address is two less than the content of register SP.  The content of
            # register SP is decremented by two.
            # 3 cycles 11 states
            ret_str = "PUSH AF"
        return ret_str, 1, 3, 11

    def _POP(self, opcode, cur_addr):
        rp = (opcode >> 4) & 0x3
        if rp != 0x3:
            # POP rp
            # The content of the memory location, whose address is specified by the content of register SP, is
            # moved to the low-order register of register pair rp.  THe content of the memory location, whose
            # address is one more than teh content of register SP, is moved to the high-order register of register
            # pair rp.  The content of register SP is incremented by 2.  Note: Register pair rp = SP may not be
            # specified.
            # 3 cycles 10 states
            ret_str = "POP {}".format(rp_translation[rp])
        else:
            # POP PSW
            # Pop processor status word
            # The content of the memory location whose address is specified by the content of register SP is used
            # to restore teh condition flags.  THe content of the memory location whose address is one more than the
            # content of register SP is moved to register A.  The content of register SP is incremented by 2.
            # 3 cycles 10 states
            ret_str = "POP AF"
        return ret_str, 1, 3, 10

    def _XTHL(self, opcode, cur_addr):
        # XTHL
        # Exchange stack top with H and L
        # The content of the L register is exchanged with the content of the memory location whose address is
        # specified by the content of register SP.  The content of the H register is exchanged with the content
        # of the memory location whose address is one more than the content of register SP.
        # 5 cycles 18 states
        return "XTHL", 1, 5, 18

    def _SPHL(self, opcode, cur_addr):
        # SPHL
        # Move HL to SP
        # The contents of registers H and L (16 bits) are moved to register SP.
        # 1 cycle 5 states
        return "SPHL", 1, 1, 5

    def _IN(self, opcode, cur_addr):
        # IN port
        # Input
        # The data placed on thh eight bit bi-directional data bus by the specified port is moved to register A.
        # 3 cycles 10 states
        ret_str = "IN A, (INP {})".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 3, 10

    def _OUT(self, opcode, cur_addr):
        # OUT port
        # Output
        # The content of register A is placed on the eight bit bi-directional data bus for transmission to the
        # specified port.
        # 3 cycles 10 states
        ret_str = "OUT (OUT ${}), A".format(hexy(self.memory[cur_addr + 1], 2))
        return ret_str, 2, 3, 10

    def _EI(self, opcode, cur_addr):
        # EI
        # Enable Interrupts
        # The interrupt system is enabled following the execution of the next instruction.
        # (Presumably, the instruction following EI)
        # 1 cycle 4 states
        return "EI", 1, 1, 4

    def _DI(self, opcode, cur_addr):
        # DI
        # Disable Interrupts
        # The interrupt system is enabled immediately following the execution of the DI instruction.
        # 1 cycle 4 states
        return "DI", 1, 1, 4

    def _HLT(self, opcode, cur_addr):
        # HLT
        # Halt
        # The processor is stopped.  The registers and flags are unaffected
        # 1 cycle 7 states
        return "HLT", 1, 1, 7

    def _NOP(self, opcode, cur_addr):
        # NOP
        # No operation is performed.  The registers and flags are unaffected.
        # 1 cycle 4 states
        return "NOP", 1, 1, 4

    def InvalidOpCode(self, opcode, cur_addr):
        raise DisassemblyNotImplementedException("Invalid opcode: {}".format(opcode))

    def disassemble(self, start_addr, max_addr, point_addr=None, breakpoint_list=[]):
        # point_addr = address which will receive a pointer next to it

        cur_addr = start_addr
        ret_str = ""
        while cur_addr <= max_addr:
            opcode = self.memory[cur_addr]
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
        return ret_str
