from array import array


class InvalidOpCodeException(Exception):
    pass


class OpcodeNotImplementedException(Exception):
    pass


class InvalidInterruptException(Exception):
    pass


# Cannot figure out how to make this a member variable of the CPU itself without creating a bunch of named functions
# translation of "ccc:"
#   0 = NZ (not zero); 1 = Z (zero); 2 = NC (no carry); 3 = C (carry)
#   4 = PO (parity odd); 5 = PE (parity even); 6 = P (plus); 7 = M (minus)
CPU_CONDITION_TEST = [lambda cpu:not cpu.zero_flag, lambda cpu:cpu.zero_flag,
                      lambda cpu:not cpu.carry_flag, lambda cpu:cpu.carry_flag,
                      lambda cpu:not cpu.parity_flag, lambda cpu:cpu.parity_flag,
                      lambda cpu:not cpu.sign_flag, lambda cpu:cpu.sign_flag]


class I8080cpu:

    def __init__(self, motherboard):

        self.motherboard = motherboard

        # program counter
        self.pc = 0x0

        # stack pointer
        self.sp = 0x0
        # used for debugger to print the stack.  Stack is set in code.  Whenever there is an explicit set to SP,
        # we will update this.  It will not get updated if you manually increment or decrement SP, only with a LD of SP
        self.stack_pointer_start = 0x0

        # There are seven 8-bit registers:  b, c, d, e, h, l, and the accumulator (a).  The opcodes that reference
        # them use the numbers 0-5 for b, c, d, e, h, l and 7 for a.  6 is not used.  For performance reasons it 
        # will be faster to access by an array, and there is an extra "register" created in the array at position 6.
        self.registers = array('B', [0 for _ in range(8)])

        # Tracking whether interrupts are enabled.  Interrupts can be disabled via the DI opcode, but the
        # interrupt bit is also cleared whenever an interrupt is triggered.  So interrupt handlers have to
        # re-enable interrupts via the EI opcode.
        self.enable_interrupts_after_next_instruction = False
        self.interrupts_enabled = True

        # If the CPU is halted, it will only handle interrupts
        self.halted = False

        # Flags - these are single-bit flip-flops in the 8080.
        # zero, carry, sign, parity, auxiliary carry
        # Not Zero = 0; Zero = 1
        self.zero_flag = False
        # No Carry = 0; Carry = 1
        self.carry_flag = False
        # Plus/Positive = 0; Minus/Negative = 1
        self.sign_flag = False
        # Parity Odd = 0; Parity Even = 1
        # NOTE: According to i8080 documentation, the parity flag is based on the number of bits that are set in
        # the byte - 00010001 is even parity even though it is an odd number (17 in base 10).  However, according to
        # https://en.wikipedia.org/wiki/Parity_flag, x86 processors changed so it looks at whether the least significant
        # bit is set - so the flag set means the number is odd, and the flag reset (meaning it is 0) means the
        # number is even.  I have seen many other 8080 emulators use this definition of parity flag.  My inference is
        # that parity flag is not used in the Space Invaders game, so emulators for that game are not impacted by
        # the incorrectness of their calculations of the flag.
        self.parity_flag = False
        self.auxiliary_carry_flag = False

        # Using a list of functions to speed the lookup, vs. doing a big nested
        # if/else.
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

        # Next three are indexed based on valid values of rp.
        self.set_register_pair = [self.set_bc, self.set_de, self.set_hl, self.set_sp]
        self.set_register_pair_as_word = [self.set_bc_as_word, self.set_de_as_word, self.set_hl_as_word,
                                          self.set_sp_as_word]
        self.get_register_pair = [self.get_bc, self.get_de, self.get_hl, self.get_sp]

    def set_zero_sign_parity_from_byte(self, n):
        if n == 0:
            self.zero_flag = True
        else:
            self.zero_flag = False

        # Per the Assembly Language Programming Manual, the sign flag is set to the value of bit 7
        if n & 0x80:
            self.sign_flag = True
        else:
            self.sign_flag = False

        # http://www.graphics.stanford.edu/~seander/bithacks.html#ParityParallel
        # Assumes n is a byte.  If we have to compute on a 16-bit value we need more shifts.
        v = n ^ (n >> 4)
        v &= 0xf
        # Note the below shift treats 1 as odd and 0 as even; but the parity bit is set with False is odd and True
        # is even.
        self.parity_flag = (((0x6996 >> v) & 1) == 0)

    def get_byte_from_flags(self):
        # Because there are only 5 condition flags, PUSH PWS formats the flags into an eight-bit byte by setting bits 3
        # and 5 always to zero and bit one is always set to 1.
        retval = 0x02  # bits 3 and 5 zero, bit one is 1.
        if self.sign_flag:
            retval |= 0x80
        if self.zero_flag:
            retval |= 0x40
        if self.auxiliary_carry_flag:
            retval |= 0x10
        if self.parity_flag:
            retval |= 0x04
        if self.carry_flag:
            retval |= 0x01
        return retval

    def set_flags_from_byte(self, n):
        self.sign_flag = bool(n & 0x80)
        self.zero_flag = bool(n & 0x40)
        self.auxiliary_carry_flag = bool(n & 0x10)
        self.parity_flag = bool(n & 0x04)
        self.carry_flag = bool(n & 0x01)

    @property
    def b(self):
        return self.registers[0]
    
    @b.setter
    def b(self, new_val):
        self.registers[0] = new_val

    @property
    def c(self):
        return self.registers[1]

    @c.setter
    def c(self, new_val):
        self.registers[1] = new_val

    @property
    def d(self):
        return self.registers[2]

    @d.setter
    def d(self, new_val):
        self.registers[2] = new_val

    @property
    def e(self):
        return self.registers[3]

    @e.setter
    def e(self, new_val):
        self.registers[3] = new_val

    @property
    def h(self):
        return self.registers[4]

    @h.setter
    def h(self, new_val):
        self.registers[4] = new_val
        
    @property
    def l(self):
        return self.registers[5]
    
    @l.setter
    def l(self, new_val):
        self.registers[5] = new_val
    
    @property
    def a(self):
        return self.registers[7]
    
    @a.setter
    def a(self, new_val):
        self.registers[7] = new_val

    # Using these instead of setters / getters because I can put them in a list (set_register_pair and
    # get_register_pair and get good performance.  I couldn't figure out how to get setters and getters into a
    # list of "function pointers."
    def set_bc(self, b, c):
        self.b = b
        self.c = c

    def set_bc_as_word(self, bc):
        self.b = (bc >> 8) & 0xFF
        self.c = bc & 0xFF

    def get_bc(self):
        return (self.b << 8) | self.c

    def set_de(self, d, e):
        self.d = d
        self.e = e

    def set_de_as_word(self, de):
        self.d = (de >> 8) & 0xFF
        self.e = de & 0xFF

    def get_de(self):
        return (self.d << 8) | self.e

    def set_hl(self, h, l):
        self.h = h
        self.l = l

    def set_hl_as_word(self, hl):
        self.h = (hl >> 8) & 0xFF
        self.l = hl & 0xFF

    def get_hl(self):
        return (self.h << 8) | self.l

    def set_sp(self, high, low):
        self.sp = (high << 8) | low
        self.stack_pointer_start = self.sp

    def set_sp_as_word(self, sp):
        self.sp = sp
        self.stack_pointer_start = self.sp

    def get_sp(self):
        # needed for things like _DAD
        return self.sp

    # DATA TRANSFER GROUP #

    def _MOV(self, opcode):
        ddd = (opcode >> 3) & 0x7
        sss = opcode & 0x7
        if ddd != 0x06 and sss != 0x06:
            # MOV r1, r2
            # Move Register
            # The content of register r2 is moved to register r1
            # Flags are not affected
            # 1 cycle, 5 states
            self.registers[ddd] = self.registers[sss]
            states = 5
        elif ddd != 0x06 and sss == 0x06:
            # MOV r, M
            # Move from memory
            # The content of the memory location, whose address is in registers H and L is moved to register r
            # Flags are not affected
            # 2 cycles, 7 states
            self.registers[ddd] = self.motherboard.memory[self.get_hl()]
            states = 7
        else:  # ddd == 0x06 and sss != 0x06:
            # MOV M, r
            # Move to memory
            # The content of register r is moved to the memory location whose address is in registers H and L
            # Flags are not affected
            # 2 cycles, 7 states
            self.motherboard.memory[self.get_hl()] = self.registers[sss]
            states = 7
        return 1, states

    def _MVI(self, opcode):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            # MVI r, data
            # Move Immediate
            # The content of byte 2 of the instruction is moved to register r
            # Flags are not affected
            # 2 cycles, 7 states
            self.registers[ddd] = self.motherboard.memory[self.pc + 1]
            states = 7
        else:
            # MVI M, data
            # Move to memory immediate
            # The content of byte 2 of the instruction is moved to the memory location whose address is in
            # registers H and L
            # Flags are not affected
            # 3 cycles 10 states
            self.motherboard.memory[self.get_hl()] = self.motherboard.memory[self.pc + 1]
            states = 10
        return 2, states

    def _LXI(self, opcode):
        # LXI rp, data 16
        # Load register pair immediate
        # Byte 3 of the instruction is moved into the high-order register (rh) of the register pair rp.
        # Byte 2 of the instruction is moved into the low-order register (rl) of the register pair rp.
        # Flags are not affected.
        # 3 cycles 10 states
        rp = (opcode >> 4) & 0x3
        high_byte = self.motherboard.memory[self.pc + 2]
        low_byte = self.motherboard.memory[self.pc + 1]
        self.set_register_pair[rp](high_byte, low_byte)
        return 3, 10

    def _LDA(self, opcode):
        # LDA addr
        # Load accumulator direct
        # The content of the memory location, whose address is specified in byte 2 and byte 3 of the
        # instruction, is moved to register A.
        # Flags are not affected
        # 4 cycles 13 states
        self.a = self.motherboard.memory[(self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]]
        return 3, 13

    def _STA(self, opcode):
        # STA addr
        # Store accumulator direct
        # The content of the accumulator is moved to the memory location whose address is specified in byte 2
        # and byte 3 of the instruction
        # Flags are not affected
        # 4 cycles 13 states
        self.motherboard.memory[(self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]] = self.a
        return 3, 13

    def _LHLD(self, opcode):
        # LHLD addr
        # Load H and L direct
        # The content of the memory location, whose address is specified in byte 2 and byte 3 of the
        # instruction,is moved to register L.  The content of the memory location at the succeeding address is
        # moved to register H.
        # Flags are not affected
        # 5 cycles 16 states
        addr = (self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]
        self.l = self.motherboard.memory[addr]
        self.h = self.motherboard.memory[addr + 1]
        return 3, 16

    def _SHLD(self, opcode):
        # SHLD addr
        # Store H and L direct
        # The content of register L is moved to the memory location whose address is specified in byte 2 and
        # byte 3.  The content of register H is moved to the succeeding memory location.
        # Flags are not affected
        # 5 cycles 16 states
        addr = (self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]
        self.motherboard.memory[addr] = self.l
        self.motherboard.memory[addr + 1] = self.h
        return 3, 16

    def _LDAX(self, opcode):
        # LDAX rp
        # Load accumulator indirect
        # The content of the memory location, whose address is in the register pair rp, is moved to register
        # A.  Note only register pairs rp=B (registers B and C) or rp=D (registers D and E) may be specified.
        # 2 cycles 7 states
        self.a = self.motherboard.memory[self.get_register_pair[(opcode >> 4) & 0x1]()]
        return 1, 7

    def _STAX(self, opcode):
        # STAX rp
        # Store accumulator indirect
        # The content of register A is moved to the memory location whose address is in the register pair rp.
        # Note: only register pairs rp=B (registers B and C) or rp=D (registers D and E) may be specified.
        # 2 cycles 7 states
        self.motherboard.memory[self.get_register_pair[(opcode >> 4) & 0x1]()] = self.a
        return 1, 7

    def _XCHG(self, opcode):
        # XCHG
        # Exchange H and L with D and E
        # THe contents of registers H and L are exchanged with the contents of registers D and E
        # Flags are not affected
        # 1 cycle 4 states
        tmp_d = self.d
        tmp_e = self.e
        self.d = self.h
        self.e = self.l
        self.h = tmp_d
        self.l = tmp_e
        return 1, 4

    # ARITHMETIC GROUP #
    def do_add(self, byte, add_one_for_carry):
        # taking logic from MAME emulator
        q = self.a + byte
        if add_one_for_carry:
            q += 1
        self.set_zero_sign_parity_from_byte(q & 0xFF)
        self.carry_flag = bool((q >> 8) & 0x01)
        self.auxiliary_carry_flag = bool((self.a ^ q ^ byte) & 0x10)
        self.a = q & 0xFF

        '''
        # There is likely a better performing way to compute AC but this is easy to understand
        a_low = self.a & 0xF
        byte_low = byte & 0xF
        low_tmp = a_low + byte_low
        if add_one_for_carry:
            low_tmp += 1
        self.auxiliary_carry_flag = (low_tmp > 0xF)

        tmp = self.a + byte
        if add_one_for_carry:
            tmp += 1
        self.carry_flag = bool(tmp > 0xFF)
        self.a = tmp & 0xFF

        self.set_zero_sign_parity_from_byte(self.a)
        '''


    def do_subtraction(self, byte, subtract_one_for_borrow, store_value):
        # Executes a subtraction.  If store_value is False, then it does a CMP and does not actually save the value
        # in the accumulator.
        # https://retrocomputing.stackexchange.com/questions/5953/carry-flag-in-8080-8085-subtraction/5956#5956
        # Note that in CMP and Subtraction, the carry flag is set based on the unsigned values.

        # taking logic from MAME emulator
        q = self.a - byte
        if subtract_one_for_borrow:
            q -= 1
        self.set_zero_sign_parity_from_byte(q & 0xFF)
        self.carry_flag = bool((q >> 8) & 0x01)
        self.auxiliary_carry_flag = bool((~(self.a ^ q ^ byte)) & 0x10)
        if store_value:
            self.a = q & 0xFF

        '''
        if subtract_one_for_borrow:
            byte += 1
            byte &= 0xFF # keeps it unsigned
        tmp = (self.a - byte) & 0xFF
        self.set_zero_sign_parity_from_byte(tmp)
        if self.a < tmp:
            self.carry_flag = True
        else:
            self.carry_flag = False

        # the auxiliary_carry_flag is set as if it were addition of the twos-complement of byte.
        twos_complement = ((~byte) + 1) & 0xFF
        a_low = self.a & 0xF
        byte_low = twos_complement & 0xF
        self.auxiliary_carry_flag = bool(a_low + byte_low > 0xF)

        if store_value:
            self.a = tmp
        '''

    def _ADD(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # ADD r
            # Add register
            # The content of register r is added to the content of the accumulator.  The result is placed in the
            # accumulator.
            # 1 cycle 4 states
            self.do_add(self.registers[sss], False)
            states = 4
        else:
            # ADD M
            # Add memory
            # The content of the memory location whose address is contained in the H and L registers is added
            # to the content of the accumulator.  The result is placed in the accumulator.
            # 2 cycles 7 states
            self.do_add(self.motherboard.memory[self.get_hl()], False)
            states = 7
        return 1, states

    def _ADI(self, opcode):
        # ADI data
        # Add Immediate
        # The contents of the second byte of the instruction is added to the content of the accumulator.  The
        # result is placed in the accumulator.
        # All flags are affected
        # 2 cycles 7 states
        self.do_add(self.motherboard.memory[self.pc + 1], False)
        return 2, 7


    def _ADC(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # ADC r
            # Add register with carry
            # The content of register r and the content of the carry bit are added to the content of the
            # accumulator.  The result is placed in the accumulator.
            # All flags are affected
            # 1 cycle 4 states
            self.do_add(self.registers[sss], self.carry_flag)
            states = 4
        else:
            # ADC M
            # Add memory with carry
            # The content of the memory location whose address is contained in the H and L registers is added
            # and the content of the CY flag are added to the content of the accumulator.  The result is placed
            # in the accumulator.
            # All flags are affected
            # 2 cycles 7 states
            self.do_add(self.motherboard.memory[self.get_hl()], self.carry_flag)
            states = 7
        return 1, states

    def _ACI(self, opcode):
        # ACI data
        # Add immediate with carry
        # The content of the second byte of the instruction and the content of the CY flag are added to the
        # contents of the accumulator.  The result is placed in the accumulator.
        # All flags are affected
        # 2 cycles 7 states
        self.do_add(self.motherboard.memory[self.pc + 1], self.carry_flag)
        return 2, 7

    def _SUB(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # SUB r
            # Subtract register
            # The content of register r is subtracted from the content of the accumulator.  The result is placed in
            # the accumulator.
            # All flags are affected
            # 1 cycle 4 states
            self.do_subtraction(self.registers[sss], False, True)
            states = 4
        else:
            # SUB M
            # Subtract memory
            # The content of the memory location whose address is contained in the H and L registers is subtracted
            # from the content of the accumulator.  The result is placed in the accumulator.
            # All flags are affected
            # 2 cycles 7 states
            self.do_subtraction(self.motherboard.memory[self.get_hl()], False, True)
            states = 7
        return 1, states

    def _SUI(self, opcode):
        # SUI data
        # Subtract Immediate
        # The content of the second byte of the instruction is subtracted from the content of the accumulator.
        # The result is placed in the accumulator.
        # All flags are affected
        # 2 cycles 7 states
        self.do_subtraction(self.motherboard.memory[self.pc + 1], False, True)
        return 2, 7

    def _SBB(self, opcode):
        sss = opcode & 0x7

        if sss != 0x6:
            # SBB r
            # Subtract register with borrow
            # The content of register r and the content of the CY flag are both subtracted from the
            # accumulator.  The result is placed in the accumulator.
            # 1 cycle 4 states
            self.do_subtraction(self.registers[sss], self.carry_flag, True)
            states = 4
        else:
            # SBB M
            # Subtract memory with borrow
            # The content of the memory location whose address is contained in the H and L registers
            # and the content of the CY flag are both subtracted from the accumulator.  The result is placed
            # in the accumulator.
            # 2 cycles 7 states
            self.do_subtraction(self.motherboard.memory[self.get_hl()], self.carry_flag, True)
            states = 7
        return 1, states

    def _SBI(self, opcode):
        # SBI data
        # Subtract immediate with borrow
        # The content of the second byte of the instruction and the contents of the CY flag are both subtracted
        # from the accumulator.  The result is placed in the accumulator.
        # 2 cycles 7 states
        self.do_subtraction(self.motherboard.memory[self.pc + 1], self.carry_flag, True)
        return 2, 7

    def _INR(self, opcode):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            # INR r
            # Increment Register
            # The content of register r is incremented by one.  Note: All condition flags except CY are affected.
            # 1 cycle 5 states
            new_val = (self.registers[ddd] + 1) & 0xFF
            self.registers[ddd] = new_val
            states = 5
        else:
            # INR M
            # Increment Memory
            # The content of the memory location whose address is contained in the H and L registers is incremented
            # by one.  Note: All condition flags except CY are affected.
            # 3 cycles 10 states
            new_val = (self.motherboard.memory[self.get_hl()] + 1) & 0xFF
            self.motherboard.memory[self.get_hl()] = new_val
            states = 10
        self.set_zero_sign_parity_from_byte(new_val)
        self.auxiliary_carry_flag = bool((new_val & 0x0F) == 0x00)
        return 1, states

    def _DCR(self, opcode):
        ddd = (opcode >> 3) & 0x7
        if ddd != 0x6:
            # DCR r
            # Decrement Register
            # The content of register r is decremented by one.  Note: All condition flags except CY are affected.
            # 1 cycle 5 states
            new_val = (self.registers[ddd] - 1) & 0xFF
            self.registers[ddd] = new_val
            states = 5
        else:
            # DCR M
            # Decrement Memory
            # The content of the memory location whose address is contained in the H and L registers is decremented
            # by one.  Note: All condition flags except CY are affected.
            # 3 cycles 10 states
            new_val = (self.motherboard.memory[self.get_hl()] - 1) & 0xFF
            self.motherboard.memory[self.get_hl()] = new_val
            states = 10

        self.set_zero_sign_parity_from_byte(new_val)
        # Based on what I see in other emulators (e.g. MAME), the AC flag is set if a borrow was needed.
        self.auxiliary_carry_flag = not bool((new_val & 0xF) == 0xF)
        return 1, states

    def _INX(self, opcode):
        # INX rp
        # Increment register pair
        # The content of the register pair rp is incremented by one.  No condition flags are affected.
        # 1 cycle 5 states
        rp = (opcode >> 4) & 0x3
        self.set_register_pair_as_word[rp]((self.get_register_pair[rp]() + 1) & 0xFFFF)
        return 1, 5

    def _DCX(self, opcode):
        # DCX rp
        # Decrement register pair
        # The content of the register pair rp is decremented by one.  No condition flags are affected.
        # 1 cycle 5 states
        rp = (opcode >> 4) & 0x3
        self.set_register_pair_as_word[rp]((self.get_register_pair[rp]() - 1) & 0xFFFF)
        return 1, 5

    def _DAD(self, opcode):
        # DAD rp
        # Add register pair to H and L
        # The content of the register pair rp is added to the register pair H and L.  THe result is placed in
        # the register pair H and L.  Note: Only the CY flag is affected.  If is set if there is a carry out
        # of the double precision add; otherwise it is reset.
        # Only the CY flag is affected, and only if there is a carry out of the 16-bit addition.
        # The Programming manual notes - DAD HL (rp 0x2) is, in effect HL = 2xHL - or a left shift by 1.  However
        # I don't think it would be any faster here to take advantage of that, as it would take an extra branch.
        # 3 cycles 10 states
        rp = (opcode >> 4) & 0x3
        new_val = self.get_hl() + self.get_register_pair[rp]()
        if new_val > 0xFFFF:
            self.carry_flag = True
        else:
            self.carry_flag = False
        self.set_hl_as_word(new_val & 0xFFFF)
        return 1, 10

    def _DAA(self, opcode):
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

        # copying the MAME logic
        wz = self.a
        if (self.auxiliary_carry_flag or (self.a & 0xF > 0x9)):
            wz += 0x06
        if (self.carry_flag or (self.a > 0x99)):
            wz += 0x60
        self.carry_flag = bool(self.carry_flag or (self.a > 0x99))
        self.auxiliary_carry_flag = bool((self.a ^ wz) & 0x10)
        self.a = wz & 0xFF
        self.set_zero_sign_parity_from_byte(self.a)



        '''
        if (self.a & 0x0F) > 0x09 or self.auxiliary_carry_flag:
            # if we don't go through this branch, self.auxiliary_carry_flag is already false and cannot become true,
            # so we only need to set it in this branch.
            tmp = self.a + 0x06
            self.auxiliary_carry_flag = bool(tmp & 0x10)
            self.a = tmp & 0xFF
        if (self.a & 0xF0) > 0x90 or self.carry_flag:
            # if we don't go through this branch, self.carry_flag is already false and cannot become true, so we only
            # need to set it in this branch.
            tmp = self.a + 0x60
            self.carry_flag = tmp > 0xFF
            self.a = tmp & 0xFF
        self.set_zero_sign_parity_from_byte(self.a)
        '''
        return 1, 4


    # LOGICAL GROUP

    def do_and(self, byte):
        # per https://retrocomputing.stackexchange.com/questions/14977/auxiliary-carry-and-the-intel-8080s-logical-instructions
        # The Auxiliary Carry flag is set to the or of bit 3 (0x08) of the 2 values involved in the AND operation.
        self.auxiliary_carry_flag = bool((self.a | byte) & 0x08)
        self.a &= byte
        self.carry_flag = False
        self.set_zero_sign_parity_from_byte(self.a)

    def do_xor(self, byte):
        self.a ^= byte
        self.auxiliary_carry_flag = False
        self.carry_flag = False
        self.set_zero_sign_parity_from_byte(self.a)

    def do_or(self, byte):
        self.a |= byte
        self.auxiliary_carry_flag = False
        self.carry_flag = False
        self.set_zero_sign_parity_from_byte(self.a)

    def _ANA(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # ANA r
            # AND register
            # The content of register r is logically anded with teh content of the accumulator.  The result is
            # placed in the accumulator.  The CY flag is cleared.
            # 1 cycle 4 states
            self.do_and(self.registers[sss])
            states = 4
        else:
            # ANA M
            # AND memory
            # THe contents of the memory location whose address is contained in the H and L registers is logically
            # anded with the content of the accumulator.  The result is placed in the accumulator.  The CY flag is
            # cleared.
            # 2 cycles 7 states
            self.do_and(self.motherboard.memory[self.get_hl()])
            states = 7
        return 1, states

    def _ANI(self, opcode):
        # ANI data
        # AND immediate
        # The content of the second byte of the instruction is logically anded with the contents of the
        # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
        # Note there is a conflict between the Assembly Language Programming Manual (which says the AC flag is
        # set same as ANA) and the Intel 8080 MIcrocomputer Systems User's Manual which says the AC flag is cleared.
        # The CPU test suites expect it to be set so I am doing it that way.
        # 2 cycles 7 states
        self.do_and(self.motherboard.memory[self.pc + 1])
        return 2, 7

    def _XRA(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # XRA r
            # Exclusive OR register
            # The content of register r is logically exclusive-or'd with the content of the accumulator.  The result
            # is placed in the accumulator.  The CY and AC flags are cleared.
            # 1 cycle 4 states
            self.do_xor(self.registers[sss])
            states = 4
        else:
            # XRA M
            # Exclusive OR memory
            # THe contents of the memory location whose address is contained in the H and L registers is exclusive-
            # OR'd with the content of the accumulator.  The result is placed in the accumulator.  The AC and CY
            # flags are cleared.
            # 2 cycles 7 states
            self.do_xor(self.motherboard.memory[self.get_hl()])
            states = 7
        return 1, states

    def _XRI(self, opcode):
        # XRI data
        # Exclusive OR immediate
        # The content of the second byte of the instruction is exclusive-OR'd with the content of the
        # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
        # 2 cycles 7 states
        self.do_xor(self.motherboard.memory[self.pc + 1])
        return 2, 7

    def _ORA(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # ORA r
            # OR register
            # The content of register r is logically inclusive-or'd with the content of the accumulator.  The result
            # is placed in the accumulator.  The CY and AC flags are cleared.
            # 1 cycle 4 states
            self.do_or(self.registers[sss])
            states = 4
        else:
            # ORA M
            # OR memory
            # THe contents of the memory location whose address is contained in the H and L registers is inclusive-
            # OR'd with the content of the accumulator.  The result is placed in the accumulator.  The AC and CY
            # flags are cleared.
            # 2 cycles 7 states
            self.do_or(self.motherboard.memory[self.get_hl()])
            states = 7
        return 1, states

    def _ORI(self, opcode):
        # ORI data
        # OR immediate
        # The content of the second byte of the instruction is inclusive-OR'd with the content of the
        # accumulator.  The result is placed in the accumulator.  The CY and AC flags are cleared.
        # 2 cycles 7 states
        self.do_or(self.motherboard.memory[self.pc + 1])
        return 2, 7

    def _CMP(self, opcode):
        sss = opcode & 0x7
        if sss != 0x6:
            # CMP r
            # Compare Register
            # The content of register r is subtracted from the accumulator.  The accumulator remains unchanged.
            # The condition flags are set as a result of the subtraction.  The Z flag is set to 1 if (A) = (r).
            # The CY flag is set to 1 if (A) < (r)
            # 1 cycle 4 states
            self.do_subtraction(self.registers[sss], False, False)
            states = 4
        else:
            # CMP M
            # Compare memory
            # The content of the memory location whose address is contained in the H and L registers is subtracted
            # from the accumulator.  The accumulator remains unchanged.  The condition lfags are set as a result
            # of the subtraction.  The Z flag is set to 1 if (A) = ((H)(L)).  The CY flag is set to 1 if (A) <
            # ((H)(L)).
            # 2 cycles 7 states
            self.do_subtraction(self.motherboard.memory[self.get_hl()], False, False)
            states = 7
        return 1, states

    def _CPI(self, opcode):
        # CPI data
        # Compare immediate
        # THe content of the second byte of the instruction is subtracted from the accumulator.  The condition
        # flags are set by the result of the subtraction.  The Z flag is set to 1 if (A) = (byte 2).  The CY
        # flag is set to 1 if (A) < (byte 2).
        # NOTE: My inference is that A is unchanged, even though this isn't stated.
        # 2 cycles 7 states
        self.do_subtraction(self.motherboard.memory[self.pc + 1], False, False)
        return 2, 7

    def _RLC(self, opcode):
        # RLC
        # Rotate left
        # The content of the accumulator is rotated left one position.  The low order bit and the CY flag are
        # both set to the value shifted out of the high order bit position.  Only the CY flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        self.carry_flag = bool(self.a & 0x80)
        self.a = (self.a << 1) & 0xFF
        if self.carry_flag:
            self.a |= 0x01
        return 1, 4

    def _RRC(self, opcode):
        # RRC
        # Rotate right
        # The content of the accumulator is rotated right one position.  The high order bit and the CY flag are
        # both set to the value shifted out of the low order bit position.  Only the CY flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        self.carry_flag = bool(self.a & 0x1)
        self.a = self.a >> 1
        if self.carry_flag:
            self.a |= 0x80
        self.a &= 0xFF
        return 1, 4

    def _RAL(self, opcode):
        # RAL
        # Rotate left through carry
        # The content of the accumulator is rotated left one position.  The low order bit is set equal to the
        # CY flag and the CY flag is set to the value shifted out of the high order bit position.  Only the CY
        # flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        old_carry_flag = self.carry_flag
        self.carry_flag = bool(self.a & 0x80)
        self.a = (self.a << 1) & 0xFF
        if old_carry_flag:
            self.a |= 0x01
        self.a &= 0xFF
        return 1, 4

    def _RAR(self, opcode):
        # RAR
        # Rotate right through carry
        # The content of the accumulator is rotated right one position.  The high order bit is
        # set to the CY flag and the CY flag is set to the value shifted out of the low order bit position.
        # Only the CY flag is affected.
        # NOTE: They mean that "of the flags, only CY flag is affected."
        # 1 cycle 4 states
        old_carry_flag = self.carry_flag
        self.carry_flag = bool(self.a & 0x1)
        self.a = self.a >> 1
        if old_carry_flag:
            self.a |= 0x80
        self.a &= 0xFF
        return 1, 4

    def _CMA(self, opcode):
        # CMA
        # Complement accumulator
        # The contents of the accumulator are complemented (zero bits become 1, one bits become 0).  No flags
        # are affected.
        # 1 cycle 4 states
        self.a = (~self.a) & 0xFF  # the and is likely not needed, but this preserves the unsigned nature of a.
        return 1, 4

    def _CMC(self, opcode):
        # CMC
        # The CY flag is complemented.  No other flags are affected.
        # 1 cycle 4 states
        self.carry_flag = not self.carry_flag
        return 1, 4

    def _STC(self, opcode):
        # STC
        # The CY flag is set to 1.  No other flags are affected.
        # 1 cycle 4 states
        self.carry_flag = True
        return 1, 4

    # BRANCH GROUP

    def _JMP(self, opcode):
        global CPU_CONDITION_TEST

        if opcode == 0xC3:
            # JMP addr
            # Control is transferred to the instruction whose address is specified in byte 3 and byte 2 of
            # the current instruction
            # Flags are not affected
            # 3 cycles 10 states
            # Because this updates PC, return 0 for pc_increments so that the cycle() function does not further
            # increment PC.
            self.pc = (self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]
            pc_increments = 0
        else:
            # JMP condition addr
            # If the specified condition is true, control is transferred to the instruction whose address is
            # specified in byte 3 and byte 2 of the current instruction; otherwise, control continues sequentially.
            # Flags are not affected
            # 3 cycles 10 states
            if CPU_CONDITION_TEST[(opcode >> 3) & 0x7](self):
                self.pc = (self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]
                pc_increments = 0
            else:
                pc_increments = 3  # skip past the 2 byte address
        return pc_increments, 10

    def _CALL(self, opcode):
        global CPU_CONDITION_TEST

        if opcode == 0xCD:
            # CALL addr
            # The high-order 8 bits of the next instruction address are moved to the memory address that is one
            # less than the content of register SP.  The low order 8 bits of the next instruction address are moved
            # to the memory location whose address is two less than the content of register SP.  THe content of
            # register SP is decremented by 2.  Control is transferred to the instruction whose address is specified
            # in byte 3 and byte 2 of the current instruction.
            # So basically - (SP) gets PC + 3 / PC + 4, decrement SP, jump to the address specified in bytes 2 & 3
            # Flags are not affected.
            # 5 cycles 17 states
            self.motherboard.memory[self.sp - 1] = ((self.pc + 3) >> 8)
            self.motherboard.memory[self.sp - 2] = ((self.pc + 3) & 0xff)
            self.sp -= 2
            self.pc = (self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]
            pc_increments = 0
            states = 17
        else:
            # CALL condition addr
            # If the specified condition is true, the actions specified in the CALL instruction (see above) are
            # performed; otherwise, control continues sequentially
            # Flags are not affected
            # If condition true:  5 cycles / 17 states
            # If condition false: 3 cycles / 11 states
            if CPU_CONDITION_TEST[(opcode >> 3) & 0x7](self):
                self.motherboard.memory[self.sp - 1] = ((self.pc + 3) >> 8)
                self.motherboard.memory[self.sp - 2] = ((self.pc + 3) & 0xff)
                self.sp -= 2
                self.pc = (self.motherboard.memory[self.pc + 2] << 8) | self.motherboard.memory[self.pc + 1]
                pc_increments = 0
                states = 17
            else:
                pc_increments = 3
                states = 11
        return pc_increments, states

    def _RET(self, opcode):
        global CPU_CONDITION_TEST

        if opcode == 0xC9:
            # RET
            # THe content of the memory location whose address is specified in register SP is moved to the low
            # order eight bits of register PC.  The content of the memory location whose address is one more than
            # the content of register SP is moved to the high-order 8 bits of register PC.  THe content of register
            # SP is incremented by 2.
            # Flags are not affected
            # 3 cycles 10 states
            self.pc = (self.motherboard.memory[self.sp + 1] << 8) | self.motherboard.memory[self.sp]
            self.sp += 2
            pc_increments = 0
            states = 10
        else:
            # RET condition
            # If the specified condition is true, the actions specified in the RET instruction (see above) are
            # performed; otherwise, control continues sequentially.
            # Flags are not affected
            # If condition true: 3 cycles / 11 states
            # If condition false: 1 cycles / 5 states
            if CPU_CONDITION_TEST[(opcode >> 3) & 0x7](self):
                self.pc = (self.motherboard.memory[self.sp + 1] << 8) | self.motherboard.memory[self.sp]
                self.sp += 2
                pc_increments = 0
                states = 11
            else:
                pc_increments = 1
                states = 5
        return pc_increments, states

    def _RST(self, opcode):
        # RST n
        # Restart
        # The high-order eight bits of the next instruction address are moved to the memory location whose
        # address is one less than the content of register SP.  THe low-order eight bits of the next instruction
        # address are moved to the memory location whose address is two less than the content of register SP.
        # THe content of register SP is decremented by two.  Control is transferred to the instruction whose
        # address is 8 times the content of NNN.
        # Note the shortcut here is to set PC = (opcode & 0x38)
        # 3 cycles 11 states

        # TODO This looks like a CALL, could refactor
        self.motherboard.memory[self.sp - 1] = (self.pc >> 8)
        self.motherboard.memory[self.sp - 2] = (self.pc & 0xff)
        self.sp -= 2

        # This is RST-specific
        self.pc = opcode & 0x38
        self.interrupts_enabled = False
        return 0, 11

    def do_interrupt(self, interrupt):
        if not (0 <= interrupt <= 7):
            raise InvalidInterruptException(interrupt)
        if self.interrupts_enabled:
            # RST instruction has binary format 11nnn111 where nnn is the interrupt number from 0-7
            opcode = 0xC7 | (interrupt << 3)
            ignore_increments, num_cycles = self.opcode_lookup[opcode](opcode)
            return num_cycles

    def _PCHL(self, opcode):
        # PCHL
        # Jump H and L indirect - move H and L to PC
        # The content of register H is moved to the high-order eight bits of register PC.  The content of
        # register L is moved to the low-order eight bits of register PC
        # Flags are not affected
        # 1 cycle 5 states
        self.pc = self.get_hl()
        return 0, 5

    # STACK, I/O, and MACHINE CONTROL GROUP

    def _PUSH(self, opcode):
        rp = (opcode >> 4) & 0x3
        if rp != 0x3:
            # PUSH rp
            # The content of the high-order register of register pair rp is moved to the memory location whose
            # address is one less than the content of register SP.  The content of the low-order register of
            # register pair rp is moved to the memory location whose address is two less than the content of
            # register SP.  The content of register SP is decremented by 2.  Note: Register pair rp = SP may
            # not be specified
            # Flags are not affected
            # 3 cycles 11 states
            tmp = self.get_register_pair[rp]()
            self.motherboard.memory[self.sp - 1] = tmp >> 8
            self.motherboard.memory[self.sp - 2] = tmp & 0xFF
        else:
            # PUSH PSW
            # Push processor status word
            # Note - rp == 0x3 is same as rp_translation[rp] == "SP", but we're not actually pushing SP
            # The content of register A is moved to the memory location whose address is one less than register SP.
            # The contents of the condition flags are assembled into a processor status word and the word is moved
            # to the memory location whose address is two less than the content of register SP.  The content of
            # register SP is decremented by two.
            #
            # ref: https://retrocomputing.stackexchange.com/questions/12300/bit-one-of-the-intel-8080s-flags-register
            # In silicon, the flags were individual flip/flops.  In the 8008, the only way to access the flags was via
            # conditional instructions.  However, the PUSH PSW added to the 8080 allowed for a register-like view.
            # There are only 5 flags, so there are 3 bits added for padding:
            # lsb = Carry, then in order: a bit fixed at 1, Parity, a bit fixed at 0, Auxiliary Carry, a bit fixed at 0,
            # Zero, and then msb = Sign.
            #
            # Flags are not affected.
            # 3 cycles 11 states
            self.motherboard.memory[self.sp - 1] = self.a
            self.motherboard.memory[self.sp - 2] = self.get_byte_from_flags()
        self.sp -= 2
        return 1, 11

    def _POP(self, opcode):
        rp = (opcode >> 4) & 0x3
        if rp != 0x3:
            # POP rp
            # The content of the memory location, whose address is specified by the content of register SP, is
            # moved to the low-order register of register pair rp.  THe content of the memory location, whose
            # address is one more than the content of register SP, is moved to the high-order register of register
            # pair rp.  The content of register SP is incremented by 2.  Note: Register pair rp = SP may not be
            # specified.
            # Flags are not affected
            # 3 cycles 10 states
            self.set_register_pair[rp](self.motherboard.memory[self.sp + 1], self.motherboard.memory[self.sp])
        else:
            # POP PSW
            # Pop processor status word
            # The content of the memory location whose address is specified by the content of register SP is used
            # to restore the condition flags.  The content of the memory location whose address is one more than the
            # content of register SP is moved to register A.  The content of register SP is incremented by 2.
            # All Flags are affected as they are restored from the stack.
            # 3 cycles 10 states
            self.set_flags_from_byte(self.motherboard.memory[self.sp])
            self.a = self.motherboard.memory[self.sp + 1]
        self.sp += 2
        return 1, 10

    def _XTHL(self, opcode):
        # XTHL
        # Exchange stack top with H and L
        # The content of the L register is exchanged with the content of the memory location whose address is
        # specified by the content of register SP.  The content of the H register is exchanged with the content
        # of the memory location whose address is one more than the content of register SP.
        # The stack pointer register remains unchanged following execution of the XTHL instruction.
        # Flags are not affected
        # 5 cycles 18 states
        tmp_h = self.h
        tmp_l = self.l
        self.h = self.motherboard.memory[self.sp + 1]
        self.l = self.motherboard.memory[self.sp]
        self.motherboard.memory[self.sp] = tmp_l
        self.motherboard.memory[self.sp + 1] = tmp_h
        return 1, 18

    def _SPHL(self, opcode):
        # SPHL
        # Move HL to SP
        # The contents of registers H and L (16 bits) are moved to register SP.
        # Flags are not affected
        # 1 cycle 5 states
        self.sp = self.get_hl()
        return 1, 5

    def _IN(self, opcode):
        # IN port
        # Input
        # The data placed on the eight bit bi-directional data bus by the specified port is moved to register A.
        # Flags are not affected
        # 3 cycles 10 states
        self.a = self.motherboard.handle_input(self.motherboard.memory[self.pc + 1])
        return 2, 10

    def _OUT(self, opcode):
        # OUT port
        # Output
        # The content of register A is placed on the eight bit bi-directional data bus for transmission to the
        # specified port.
        # Flags are not affected
        # 3 cycles 10 states
        #
        # https://www.computerarcheology.com/Arcade/SpaceInvaders/Hardware.html#output
        # Port 2 - bits 0, 1, 2 are the amount of the shift - see "Dedicated Shift Hardware" on the above page
        # Port 3 - Sounds
        # Port 5 - Sounds
        # Port 6 - Watchdog
        self.motherboard.handle_output(self.motherboard.memory[self.pc + 1], self.a)
        return 2, 10

    def _EI(self, opcode):
        # EI
        # Enable Interrupts
        # The interrupt system is enabled following the execution of the next instruction.
        # (Presumably, the instruction following EI)
        # 1 cycle 4 states

        self.enable_interrupts_after_next_instruction = True
        return 1, 4

    def _DI(self, opcode):
        # DI
        # Disable Interrupts
        # The interrupt system is disabled immediately following the execution of the DI instruction.
        # 1 cycle 4 states
        self.interrupts_enabled = False
        return 1, 4

    def _HLT(self, opcode):
        # HLT
        # Halt
        # The processor is stopped.  The registers and flags are unaffected
        # 1 cycle 7 states
        print ("HALT")
        self.halted = True
        return 1, 7

    def _NOP(self, opcode):
        # NOP
        # No operation is performed.  The registers and flags are unaffected.
        # 1 cycle 4 states
        return 1, 4

    def InvalidOpCode(self, opcode):
        raise InvalidOpCodeException("Invalid opcode: {}".format(opcode))


    def debug_dump(self, total_states = 0):
        ret_str = ""
        ret_str += "PC: 0x{}\n".format(hex(self.pc).zfill(4).upper()[2:])
        ret_str += "A: 0x{}\n".format(hex(self.a).zfill(2).upper()[2:])
        ret_str += "Flags: "
        if self.zero_flag:
            ret_str += "Z, "
        else:
            ret_str += "NZ, "
        if self.carry_flag:
            ret_str += "C, "
        else:
            ret_str += "NC, "
        if self.sign_flag:
            ret_str += "M, "
        else:
            ret_str += "P, "
        if self.parity_flag:
            ret_str += "PE, "
        else:
            ret_str += "PO, "
        if self.auxiliary_carry_flag:
            ret_str += "Aux C\n"
        else:
            ret_str += "Aux NC\n"
        ret_str += "SP: 0x{}\n".format(hex(self.sp).upper()[2:])
        ret_str += "B: 0x{}\t".format(hex(self.b)[2:].zfill(2).upper())
        ret_str += "C: 0x{}\n".format(hex(self.c)[2:].zfill(2).upper())
        ret_str += "D: 0x{}\t".format(hex(self.d)[2:].zfill(2).upper())
        ret_str += "E: 0x{}\n".format(hex(self.e)[2:].zfill(2).upper())
        ret_str += "H: 0x{}\t".format(hex(self.h)[2:].zfill(2).upper())
        ret_str += "L: 0x{}\n".format(hex(self.l)[2:].zfill(2).upper())

        return ret_str

    def cycle(self):
        if not self.halted:
            opcode = self.motherboard.memory[self.pc]
            # for performance reasons, we pass the opcode to the function that handles it, so we do not have to go
            # to memory twice to get it.
            flip_interrupts_on = self.enable_interrupts_after_next_instruction
            pc_increments, num_cycles = self.opcode_lookup[opcode](opcode)
            self.pc += pc_increments
            if flip_interrupts_on:
                self.interrupts_enabled = True
                self.enable_interrupts_after_next_instruction  = False
            return num_cycles
        else:
            return 0
