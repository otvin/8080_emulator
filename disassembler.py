
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

    def disassemble(self, start_addr, max_addr):
        # not trying to perform well, just trying to get it functionally accurate

        cur_addr = start_addr
        ret_str = ""
        while cur_addr <= max_addr:

            opcode = self.memory[cur_addr]
            bits1_2 = (opcode >> 6) & 0x3
            ddd = (opcode >> 3) & 0x7
            ccc = ddd
            nnn = ddd
            bits3_5 = ddd  # bits 3-5
            sss = opcode & 0x7
            bits6_8 = sss  # 3 least significant bits
            rp = (opcode >> 4) & 0x3
            low_nibble = opcode & 0xF
            ret_str += "{}: ".format(hexy(cur_addr, 4))

            # DATA TRANSFER GROUP #

            if bits1_2 == 0x1 and ddd != 0x06 and sss != 0x06:
                # MOV r1, r2
                # Move Register
                # The content of register r2 is moved to register r1
                # 1 cycle, 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "LD {}, {}".format(ddd_sss_translation[ddd], ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x1 and ddd != 0x06 and sss == 0x06:
                # MOV r, M
                # Move from memory
                # The content of the memory location, whose address is in registers H and L is moved to register r
                # 2 cycles, 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "LD {}, (HL)".format(ddd_sss_translation[ddd])
                cur_addr += 1
            elif bits1_2 == 0x1 and ddd == 0x06 and sss != 0x06:
                # MOV M, r
                # Move to memory
                # The content of register r is moved to the memory location whose address is in registers H and L
                # 2 cycles, 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "LD (HL), {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x0 and ddd_sss_translation[ddd] is not None and bits6_8 == 0x6:
                # MVI r, data
                # Move Immediate
                # The content of byte 2 of the instruction is moved to register r
                # 2 cycles, 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                # The disassembled ROM at Computer Archaeology uses "LD" for Load instead of MVI.
                ret_str += "LD {}, ${}".format(ddd_sss_translation[ddd], hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x0 and bits3_5 == 0x6 and bits6_8 == 0x6:
                # MVI M, data
                # Move to memory immediate
                # The content of byte 2 of the instruction is moved to the memory location whose address is in
                # registers H and L
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "LD (HL), ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x0 and low_nibble == 0x1:
                # LXI rp, data 16
                # Load register pair immediate
                # Byte 3 of the instruction is moved into the high-order register (rh) of the register pair rp.
                # Byte 2 of the instruction is moved into the low-order register (rl) of the register pair rp.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "LD {}, ${}{}".format(rp_translation[rp],
                                                  hexy(self.memory[cur_addr + 2], 2),
                                                  hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x0 and ddd == 0x7 and bits6_8 == 0x2:
                # LDA addr
                # Load accumulator direct
                # The content of the memory location, whose address is specified in byte 2 and byte 3 of the
                # instruction, is moved to register A.
                # 4 cycles 13 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "LD A, (${}{})".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x0 and bits3_5 == 0x6 and bits6_8 == 0x2:
                # STA addr
                # Store accumulator direct
                # The content of the accumulator is moved to the memory location whose address is specified in byte 2
                # and byte 3 of the instruction
                # 4 cycles 13 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "LD (${}{}), A".format(hexy(self.memory[cur_addr + 2], 2),
                                                  hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x0 and bits3_5 == 0x5 and bits6_8 == 0x2:
                # LHLD addr
                # Load H and L direct
                # The content of the memory location, whose address is specified in byte 2 and byte 3 of the
                # instruction,is moved to register L.  The content of the memory location at the succeeding address is
                # moved to register H.
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "LD HL, (${}{})".format(hexy(self.memory[cur_addr + 2], 2),
                                                   hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x0 and bits3_5 == 0x4 and bits6_8 == 0x2:
                # SHLD addr
                # Store H and L direct
                # The content of register L is moved to the memory location whose address is specified in byte 2 and
                # byte 3.  The content of register H is moved to the succeeding memory location.
                # 5 cycles 16 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "LD (${}{}), HL".format(hexy(self.memory[cur_addr + 2], 2),
                                                   hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x0 and (rp == 0x0 or rp == 0x1) and low_nibble == 0xA:
                # LDAX rp
                # Load accumulator indirect
                # The content of the memory location, whose address is in the register pair rp, is moved to register
                # A.  Note only register pairs rp=B (registers B and C) or rp=D (registers D and E) may be specified.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "LDAX ({})".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x0 and (rp == 0x0 or rp == 0x1) and low_nibble == 0x2:
                # STAX rp
                # Store accumulator indirect
                # The content of register A is moved to teh memory location whose address is in the register pair rp.
                # Note: only register pairs rp=B (registers B and C) or rp=D (registers D and E) may be specified.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "STAX ({})".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x5 and bits6_8 == 0x3:
                # XCHG
                # Exchange H and L with D and E
                # THe contents of registers H and L are exchanged with the contents of registers D and E
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "EX DE,HL"
                cur_addr += 1

            # ARITHMETIC GROUP #

            elif bits1_2 == 0x2 and bits3_5 == 0x0 and sss != 0x6:
                # ADD r
                # Add register
                # The content of register r is added to the content of the accumulator.  The result is placed in the
                # accumulator.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "ADD A, {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x0 and bits6_8 == 0x6:
                # ADD M
                # Add memory
                # The content of the memory location whose address is contained in the H and L registers is added
                # to the content of the accumulator.  The result is placed in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "ADD A, (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x0 and bits6_8 == 0x6:
                # ADI data
                # Add Immediate
                # The contents of the second byte of the instruction is added to the content of the accumulator.  The
                # result is placed in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "ADD A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x2 and bits3_5 == 0x1 and sss != 0x6:
                # ADC r
                # Add register with carry
                # The content of register r and the content of the carry bit are added to the content of the
                # accumulator.  The result is placed in the accumulator.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "ADC A, {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x1 and bits6_8 == 0x6:
                # ADC M
                # Add memory with carry
                # The content of the memory location whose address is contained in the H and L registers is added
                # and the content of the CY flag are added to the content of the accumulator.  The result is placed
                # in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "ADC A, (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x1 and bits6_8 == 0x6:
                # ACI data
                # Add immediate with carry
                # The content of the second byte of the instruction and the content of the CY flag are added to the
                # contents of the accumulator.  THe result is placed in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "ACI A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x2 and bits3_5 == 0x2 and sss != 0x6:
                # SUB r
                # Subtract register
                # The content of register r is subtracted from the content of the accumulator.  The result is placed in
                # the accumulator.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "SUB A, {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x2 and bits6_8 == 0x6:
                # SUB M
                # Subtract memory
                # The content of the memory location whose address is contained in the H and L registers is subtracted
                # from the content of the accumulator.  The result is placed in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "SUB A, (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x2 and bits6_8 == 0x6:
                # SUI data
                # Subtract Immediate
                # The content of the second byte of the instruction is subtracted from the content of the accumulator.
                # The result is placed in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "SUB A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x2 and bits3_5 == 0x3 and sss != 0x6:
                # SBB r
                # Subtract register with borrow
                # The content of register r and the content of the CY flag are both subtracted from the
                # accumulator.  The result is placed in the accumulator.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "SBB A, {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x3 and bits6_8 == 0x6:
                # SBB M
                # Subtract memory with borrow
                # The content of the memory location whose address is contained in the H and L registers
                # and the content of the CY flag are both subtracted from the accumulator.  The result is placed
                # in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "SBB A, (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x3 and bits6_8 == 0x6:
                # SBI data
                # Subtract immediate with borrow
                # The content of the second byte of the instruction and the contents of the CY flag are both subtracted
                # from the accumulator.  The result is placed in the accumulator.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "SBI A, ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x0 and ddd != 0x6 and bits6_8 == 0x4:
                # INR r
                # Increment Register
                # The content of register r is incremented by one.  Note: All condition flags except CY are affected.
                # 1 cycle 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "INC {}".format(ddd_sss_translation[ddd])
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x6 and bits6_8 == 0x4:
                # INR M
                # Increment Memory
                # The content of the memory location whose address is contained in the H and L registers is incremented
                # by one.  Note: All condition flags except CY are affected.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "INC (HL)"
                cur_addr += 1
            elif bits1_2 == 0x0 and ddd != 0x6 and bits6_8 == 0x5:
                # DCR r
                # Decrement Register
                # The content of register r is decremented by one.  Note: All condition flags except CY are affected.
                # 1 cycle 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "DEC {}".format(ddd_sss_translation[ddd])
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x6 and bits6_8 == 0x5:
                # DCR M
                # Decrement Memory
                # The content of the memory location whose address is contained in the H and L registers is decremented
                # by one.  Note: All condition flags except CY are affected.
                # 3 cycles 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "DEC (HL)"
                cur_addr += 1
            elif bits1_2 == 0x0 and low_nibble == 0x3:
                # INX rp
                # Increment register pair
                # The content of the register pair rp is incremented by one.  No condition flags are affected.
                # 1 cycle 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "INC {}".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x0 and low_nibble == 0xB:
                # DCX rp
                # Decrement register pair
                # The content of the register pair rp is decremented by one.  No condition flags are affected.
                # 1 cycle 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "DEC {}".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x0 and low_nibble == 0x9:
                # DAD rp
                # Add register pair to H and L
                # The content of the register pair rp is added to the register pair H and L.  THe result is placed in
                # the register pair H and L.  Note: Only the CY flag is affected.  If is set if there is a carry out
                # of the double precision add; otherwise it is reset.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "ADD HL,{}".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x4 and bits6_8 == 0x7:
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
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "DAA"
                cur_addr += 1

            #  LOGICAL GROUP #

            elif bits1_2 == 0x2 and bits3_5 == 0x4 and sss != 0x6:
                # ANA r
                # AND register
                # The content of register r is logically anded with teh content of the accumulator.  The result is
                # placed in the accumulator.  The CY flag is cleared.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "AND {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x4 and bits6_8 == 0x6:
                # ANA M
                # AND memory
                # THe contents of the memory location whose address is contained in the H and L registers is logically
                # anded with the content of the accumulator.  The result is placed in the accumulator.  The CY flag is
                # cleared.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "AND (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x4 and bits6_8 == 0x6:
                # ANI data
                # AND immediate
                # The content of the second byte of the instruction is logically anded with the contents of the
                # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "AND ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x2 and bits3_5 == 0x5 and sss != 0x6:
                # XRA r
                # Exclusive OR register
                # The content of register r is logically exclusive-or'd with the content of the accumulator.  The result
                # is placed in the accumulator.  The CY and AC flags are cleared.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "XOR {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x5 and bits6_8 == 0x6:
                # XRA M
                # Exclusive OR memory
                # THe contents of the memory location whose address is contained in the H and L registers is exclusive-
                # OR'd with the content of the accumulator.  The result is placed in the accumulator.  The AC and CY
                # flags are cleared.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "XOR (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x5 and bits6_8 == 0x6:
                # XRI data
                # Exclusive OR immediate
                # The content of the second byte of the instruction is exclusive-OR'd with the content of the
                # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "XOR ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x2 and bits3_5 == 0x6 and sss != 0x6:
                # ORA r
                # OR register
                # The content of register r is logically inclusive-or'd with the content of the accumulator.  The result
                # is placed in the accumulator.  The CY and AC flags are cleared.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "OR {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x6 and bits6_8 == 0x6:
                # ORA M
                # OR memory
                # THe contents of the memory location whose address is contained in the H and L registers is inclusive-
                # OR'd with the content of the accumulator.  The result is placed in the accumulator.  The AC and CY
                # flags are cleared.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "OR (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x6 and bits6_8 == 0x6:
                # ORI data
                # OR immediate
                # The content of the second byte of the instruction is inclusive-OR'd with the content of the
                # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "OR ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x2 and bits3_5 == 0x7 and sss != 0x6:
                # CMP r
                # Compare Register
                # The content of register r is subtracted from the accumulator.  THe accumulator remains unchanged.
                # The condition flags are set as a result of the subtraction.  The Z flag is set to 1 if (A) = (r).
                # The CY flag is set to 1 if (A) < (r)
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "CMP {}".format(ddd_sss_translation[sss])
                cur_addr += 1
            elif bits1_2 == 0x2 and bits3_5 == 0x7 and bits6_8 == 0x6:
                # CMP M
                # Compare memory
                # The content of the memory location whose address is contained in the H and L registers is subtracted
                # from the accumulator.  The accumulator remains unchanged.  The condition lfags are set as a result
                # of the subtraction.  The Z flag is set to 1 if (A) = ((H)(L)).  The CY flag is set to 1 if (A) <
                # ((H)(L)).
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "CMP (HL)"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x7 and bits6_8 == 0x6:
                # CPI data
                # Compare immediate
                # THe content of teh second byte of the instruction is subtracted from the accumulator.  The condition
                # flags are set by the result of the subtraction.  The Z flag is set to 1 if (A) = (byte 2).  The CY
                # flag is set to 1 if (A) < (byte 2).
                # NOTE: My inference is that A is unchanged, even though this isn't stated.
                # 2 cycles 7 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "CMP ${}".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x0 and bits3_5 == 0x0 and bits6_8 == 0x7:
                # RLC
                # Rotate left
                # The content of the accumulator is rotated left one position.  The low order bit and the CY flag are
                # both set to the value shifted out of the high order bit position.  Only the CY flag is affected.
                # NOTE: They mean that "of the flags, only CY flag is affected."
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RLC"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x1 and bits6_8 == 0x7:
                # RRC
                # Rotate right
                # The content of the accumulator is rotated right one position.  The high order bit and the CY flag are
                # both set to the value shifted out of the low order bit position.  Only the CY flag is affected.
                # NOTE: They mean that "of the flags, only CY flag is affected."
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RRCA"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x2 and bits6_8 == 0x7:
                # RAL
                # Rotate left through carry
                # The content of the accumulator is rotated left one position.  The low order bit is set equal to the
                # CY flag and the CY flag is set to the value shifted out of the high order bit position.  Only the CY
                # flag is affected.
                # NOTE: They mean that "of the flags, only CY flag is affected."
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RAL"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x3 and bits6_8 == 0x7:
                # RAR
                # Rotate right through carry
                # The content of the accumulator is rotated right one position.  The high order bit and the CY flag is
                # set to the CY flag and the CY flag is set to the value shifted out of the low order bit position.
                # Only the CY flag is affected.
                # NOTE: They mean that "of the flags, only CY flag is affected."
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RAR"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x5 and bits6_8 == 0x7:
                # CMA
                # Complement accumulator
                # The contents of the accumulator are complemented (zero bits become 1, one bits become 0).  No flags
                # are affected.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "CMA"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x7 and bits6_8 == 0x7:
                # CMC
                # The CY flag is complemented.  No other flags are affected.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "CMC"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x6 and bits6_8 == 0x7:
                # STC
                # The CY flag is set to 1.  No other flags are affected.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "STC"
                cur_addr += 1

            #  BRANCH GROUP #

            elif bits1_2 == 0x3 and bits3_5 == 0x0 and bits6_8 == 0x3:
                # JMP addr
                # Control is transferred to the instruction whose address is specified in byte 3 and byte 2 of
                # the current instruction
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "JMP ${}{}".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x3 and bits6_8 == 0x2:
                # JMP condition addr
                # If the specified condition is true, control is transferred to the instruction whose address is
                # specified in byte 3 and byte 2 of the current instruction; otherwise, control continues sequentially.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "JMP {} ${}{}".format(ccc_translation[ccc],
                                                 hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x3 and bits3_5 == 0x1 and bits6_8 == 0x5:
                # CALL addr
                # The high-order 8 bits of the next instruction address are moved to the memory address that is one
                # less than the content of register SP.  The low order 8 bits of the next instruction address are moved
                # to the memory location whose address is two less than the content of register SP.  THe content of
                # register SP is decremented by 2.  Control is transferred to the instruction whose address is specified
                # in byte 3 and byte 2 of the current instruction.
                # So basically - (SP) gets PC + 3 / PC + 4, decrement SP, jump to the address specified in bytes 2 & 3
                # 5 cycles 17 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "CALL ${}{}".format(hexy(self.memory[cur_addr + 2], 2), hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x3 and bits6_8 == 0x4:
                # CALL condition addr
                # If the specified condition is true, the actions specified in the CALL instruction (see above) are
                # performed; otherwise, control continues sequentially
                # If condition true:  5 cycles / 17 states
                # If condition false: 3 cycles / 11 states
                ret_str += get_opcode_display(self.memory, cur_addr, 3)
                ret_str += "CALL {} ${}{}".format(ccc_translation[ccc],
                                                  hexy(self.memory[cur_addr + 2], 2),
                                                  hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 3
            elif bits1_2 == 0x3 and bits3_5 == 0x1 and bits6_8 == 0x1:
                # RET
                # THe content of the memory location whose address is specified in register SP is moved to the low
                # order eight bits of register PC.  THe content of the memory location whose address is one more than
                # the content of register SP is moved to the high-order 8 bits of register PC.  THe content of register
                # SP is incremented by 2.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RET"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits6_8 == 0x0:
                # RET condition
                # If the specified condition is true, the actions specified in the RET instruction (see above) are
                # performed; otherwise, control continues sequentially.
                # If condition true: 3 cycles / 11 states
                # If condition false: 1 cycles / 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RET {}".format(ccc_translation[ccc])
                cur_addr += 1
            elif bits1_2 == 0x3 and bits6_8 == 0x7:
                # RST n
                # Restart
                # The high-order eight bits of the next instruction address are moved to the memory location whose
                # address is one less than the content of register SP.  THe low-order eight bits of the next instruction
                # address are moved to the memory location whose address is two less than the content of register SP.
                # THe content of register SP is decremented by two.  Control is transferred to teh instruction whose
                # address is 8 times the content of NNN.
                # Note the shortcut here is to set PC = 00 + (opcode & 0x56)
                # 3 cycles 11 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "RST {}".format(hexy(nnn, 3))
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x5 and bits6_8 == 0x1:
                # PCHL
                # Jump H and L indirect - move H and L to PC
                # The content of register H is moved to teh high-order eight bits of register PC.  The content of
                # register L is moved to the low-order eight bits of register PC
                # 1 cycle 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "PCHL"
                cur_addr += 1

            # STACK, I/O, and MACHINE CONTROL GROUP

            elif bits1_2 == 0x3 and rp != 0x3 and low_nibble == 0x5:
                # PUSH rp
                # The content of thh high-order register of register pair rp is moved to the memory location whose
                # address is one less than the content of register SP.  The content of the low-order register of
                # register pair rp is moved to the memory location whose address is two less than the content of
                # register SP.  The content of register SP is decremented by 2.  Note: Register pair rp = SP may
                # not be specified
                # 3 cycles 11 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "PUSH {}".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x3 and rp == 0x3 and low_nibble == 0x5:
                # PUSH PSW
                # Push processor status word
                # Note - rp == 0x3 is same as rp_translation[rp] == "SP", but we're not actually pushing SP
                # The content of register A is moved to the memory location whose address is one less than register SP.
                # The contents of the condition flags are assembled into a processor status word and the word is moved
                # to the memory location whose address is two less than the content of register SP.  The content of
                # register SP is decremented by two.
                # 3 cycles 11 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                # The disassembler at Computer Archaeology uses "AF" for "Accumulator and Flags" instead of PSW
                ret_str += "PUSH AF"
                cur_addr += 1
            elif bits1_2 == 0x3 and rp != 0x3 and low_nibble == 0x1:
                # POP rp
                # The content of the memory location, whose address is specified by the content of register SP, is
                # moved to the low-order register of register pair rp.  THe content of the memory location, whose
                # address is one more than teh content of register SP, is moved to the high-order register of register
                # pair rp.  The content of register SP is incremented by 2.  Note: Register pair rp = SP may not be
                # specified.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "POP {}".format(rp_translation[rp])
                cur_addr += 1
            elif bits1_2 == 0x3 and rp == 0x3 and low_nibble == 0x1:
                # POP PSW
                # Pop processor status word
                # The content of the memory location whose address is specified by the content of register SP is used
                # to restore teh condition flags.  THe content of the memory location whose address is one more than the
                # content of register SP is moved to register A.  The content of register SP is incremented by 2.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "POP AF"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x4 and bits6_8 == 0x3:
                # XTHL
                # Exchange stack top with H and L
                # The content of the L register is exchanged with the content of the memory location whose address is
                # specified by the content of register SP.  The content of the H register is exchanged with the content
                # of the memory location whose address is one more than the content of register SP.
                # 5 cycles 18 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "XTHL"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x7 and bits6_8 == 0x1:
                # SPHL
                # Move HL to SP
                # The contents of registers H and L (16 bits) are moved to register SP.
                # 1 cycle 5 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "SPHL"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x3 and bits6_8 == 0x3:
                # IN port
                # Input
                # The data placed on teh eight bit bi-directional data bus by the specified port is moved to register A.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "IN A, (INP {})".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x3 and bits3_5 == 0x2 and bits6_8 == 0x3:
                # OUT port
                # Output
                # The content of register A is placed on the eight bit bi-directional data bus for transmission to the
                # specified port.
                # 3 cycles 10 states
                ret_str += get_opcode_display(self.memory, cur_addr, 2)
                ret_str += "OUT (OUT ${}), A".format(hexy(self.memory[cur_addr + 1], 2))
                cur_addr += 2
            elif bits1_2 == 0x3 and bits3_5 == 0x7 and bits6_8 == 0x3:
                # EI
                # Enable Interrupts
                # The interrupt system is enabled following the execution of the next instruction.
                # (Presumably, the instruction following EI)
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "EI"
                cur_addr += 1
            elif bits1_2 == 0x3 and bits3_5 == 0x6 and bits6_8 == 0x3:
                # DI
                # Disable Interrupts
                # The interrupt system is enabled immediately following the execution of the DI instruction.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "DI"
                cur_addr += 1
            elif bits1_2 == 0x1 and bits3_5 == 0x6 and bits6_8 == 0x6:
                # HLT
                # Halt
                # The processor is stopped.  The registers and flags are unaffected
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "HLT"
                cur_addr += 1
            elif bits1_2 == 0x0 and bits3_5 == 0x0 and bits6_8 == 0x0:
                # NOP
                # No operation is performed.  The registers and flags are unaffected.
                # 1 cycle 4 states
                ret_str += get_opcode_display(self.memory, cur_addr, 1)
                ret_str += "NOP"
                cur_addr += 1
            else:
                print(ret_str + hexy(opcode, 0, True))
                raise DisassemblyNotImplementedException(hex(opcode).upper())

            ret_str += "\n"
        return ret_str