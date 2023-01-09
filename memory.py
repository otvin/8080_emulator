from array import array


class IllegalWriteException(Exception):
    pass

class MemoryOutOfBoundsException(Exception):
    pass

class Memory:
    def __init__(self):
        self.memory = None

    def __getitem__(self, key):
        return self.memory[key]

    def __setitem__(self, key, new_value):
        self.memory[key] = new_value

    def debug_dump(self, start, end):
        ret_str = "\n\nRAM:\n"
        if start % 32 != 0:
            tmp = start + (32 - (start % 32))
            ret_str += ("0x{} - 0x{}:  ".format(hex(start)[2:].zfill(4).upper(), hex(tmp)[2:].zfill(4).upper()))
        for i in range(start, end + 1):
            if i % 32 == 0:
                ret_str += "0x{} - 0x{}:  ".format(hex(i)[2:].zfill(3).upper(), hex(i + 31)[2:].zfill(3).upper())
            ret_str += hex(self.memory[i])[2:].zfill(2).upper()
            if i % 32 == 31:
                ret_str += "\n"
        return ret_str

    def max_mem(self):
        return len(self.memory)


class Test8080SystemMemory(Memory):
    def __init__(self):
        super().__init__()
        self.memory = array('B', [0 for _ in range(0x4000)])
        self.load_rom()

    def load_rom(self):
        infile = open("TST8080.COM", "rb")
        i = 0x100
        done = False
        while not done:
            next_byte = infile.read(1)
            if not next_byte:
                done = True
            else:
                self.memory[i] = int.from_bytes(next_byte, 'big')
                i += 1
        infile.close()


class SpaceInvadersMemory(Memory):
    def __init__(self):
        # per http://www.emulator101.com/memory-maps.html
        # ROMS are loaded in 0x0000 - 0x1fff
        # Working RAM is 0x2000 - 0x23ff
        # VRAM is 0x2400-0x3fff
        super().__init__()
        self.memory = array('B', [0 for _ in range(0x4000)])
        self.vram_start = 0x2400
        self.load_roms()

    def __getitem__(self, key):
        if not (0x0 <= key <= 0x5fff):
            raise MemoryOutOfBoundsException
        if key <= 0x3fff:
            return self.memory[key]
        else:
            return self.memory[key - 0x2000]

    def __setitem__(self, key, new_value):
        if not (0x0 <= key <= 0x5fff):
            raise MemoryOutOfBoundsException
        if 0x0 <= key <= 0x1fff:
            # we can only write to the roms by writing to self.memory directly.  See load_roms() below.
            raise IllegalWriteException("Cannot write to ROM value {}".format(key))

        if key <= 0x3fff:
            self.memory[key] = new_value
        else:
            self.memory[key - 0x2000] = new_value

    def debug_dump(self, start=0x0, end=0x3fff):
        super().debug_dump(start, end)

    def load_roms(self):
        # per http://www.emulator101.com/memory-maps.html the ROMs are loaded
        # $0000-$07ff:    invaders.h
        # $0800-$0fff:    invaders.g
        # $1000-$17ff:    invaders.f
        # $1800-$1fff:    invaders.e

        i = 0x0
        file_list = ["invaders.h", "invaders.g", "invaders.f", "invaders.e"]
        for file in file_list:
            infile = open(file, "rb")
            done = False
            while not done:
                next_byte = infile.read(1)
                if not next_byte:
                    done = True
                else:
                    self.memory[i] = int.from_bytes(next_byte, 'big')  # big vs. little doesn't matter on 1-byte chunks
                    i += 1
            infile.close()
        assert i == 0x2000
