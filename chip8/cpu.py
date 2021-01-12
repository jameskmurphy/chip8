import random
import time

C8_FONT = [
     bytearray([0xF0, 0x90, 0x90, 0x90, 0xF0]),  # 0
     bytearray([0x20, 0x60, 0x20, 0x20, 0x70]),  # 1
     bytearray([0xF0, 0x10, 0xF0, 0x80, 0xF0]),  # 2
     bytearray([0xF0, 0x10, 0xF0, 0x10, 0xF0]),  # 3
     bytearray([0x90, 0x90, 0xF0, 0x10, 0x10]),  # 4
     bytearray([0xF0, 0x80, 0xF0, 0x10, 0xF0]),  # 5
     bytearray([0xF0, 0x80, 0xF0, 0x90, 0xF0]),  # 6
     bytearray([0xF0, 0x10, 0x20, 0x40, 0x40]),  # 7
     bytearray([0xF0, 0x90, 0xF0, 0x90, 0xF0]),  # 8
     bytearray([0xF0, 0x90, 0xF0, 0x10, 0xF0]),  # 9
     bytearray([0xF0, 0x90, 0xF0, 0x90, 0x90]),  # A
     bytearray([0xE0, 0x90, 0xE0, 0x90, 0xE0]),  # B
     bytearray([0xF0, 0x80, 0x80, 0x80, 0xF0]),  # C
     bytearray([0xE0, 0x90, 0x90, 0x90, 0xE0]),  # D
     bytearray([0xF0, 0x80, 0xF0, 0x80, 0xF0]),  # E
     bytearray([0xF0, 0x80, 0xF0, 0x80, 0x80])   # F
]

class CPU:
    NUM_MAIN_REGISTERS = 16
    STACK_DEPTH = 16
    RAM_SIZE_BYTES = 4096
    TO_8BIT = 2 ** 8
    TO_12BIT = 2 ** 12
    TO_16BIT = 2 ** 16
    SCREEN_WIDTH = 64
    SCREEN_HEIGHT = 32
    FONT_CHAR_HEIGHT = 5
    SPRITE_WIDTH = 8
    TIMER_DEC_FREQ_HZ = 60
    TIMER_DEC_TIMESTEP_S = 1. / TIMER_DEC_FREQ_HZ
    PROGRAM_START_ADDR = 0x200

    def __init__(self, keyboard=None, screen=None):
        # User accessible registers
        self.V = bytearray(self.NUM_MAIN_REGISTERS)  # 16 x 8-bit general purpose registers
        self.I = 0              # memory address register
        self.DT = 0             # delay timer
        self.ST = 0             # sound timer

        # User inaccessible registers
        self.PC = 0x200         # program counter
        self.SP = 0             # stack pointer

        # Memory
        self.stack = [0] * self.STACK_DEPTH   # the stack, 16 x 16-bit values
        self.ram = bytearray(self.RAM_SIZE_BYTES)  # the main memory

        # Screen (externally provided)
        self.screen = screen

        # Keyboard (externally provided)
        self.keyboard = keyboard

        # initialization
        self._init_font()   # places the default font into the first bit of the RAM
        self._time_at_last_dec = time.time()  # time since the 60Hz timers were last decremented

    def print_state(self):
        for i in range(0, self.NUM_MAIN_REGISTERS, 2):
            print("V[{:2}]: {:3}          V[{:2}]: {:3}".format(i, self.V[i], i + 1, self.V[i + 1]))
        print()
        print("I:  {:3}        PC: {:5}".format(self.I, self.PC))
        print("DT: {:3}        SP: {:3}".format(self.DT, self.SP))
        print("ST: {:3}        Instr @ PC: {}".format(self.ST, self.ram[self.PC:self.PC+2].hex()))
        print()
        print("Stack: {}".format(self.stack))
        print()
        print("Memory at I: {}".format(self.ram[self.I]))
        print()
        print("Time since last dec: {:.3f}s".format(time.time() - self._time_at_last_dec))

    def _init_font(self):
        """
        Places the font into system memory
        :return:
        """
        for i, c in enumerate(C8_FONT):
            self.ram[i * 5: i * 5 + 5] = c

    def load_program(self, bytecode):
        self.ram[self.PROGRAM_START_ADDR:self.PROGRAM_START_ADDR + len(bytecode)] = bytecode

    def tick(self):
        """
        Run a single cycle of the CPU (one instruction)
        :return:
        """
        # run the instruction and increment PC
        if self.PC >= self.RAM_SIZE_BYTES - 2:
            raise ValueError("PC out of range: PC = {}    (max addr = {})".format(self.PC, self.RAM_SIZE_BYTES - 2))
        instr = self.ram[self.PC:self.PC + 2]   # instructions are two bytes
        #print(self.PC, instr.hex())
        increment_pc = self.run_instruction(instr)
        if increment_pc:
            self.PC += 2



        # if sufficient time has passed, decrement the timers
        self._update_delay_timers()

    def _update_delay_timers(self):
        """
        Decrement the delay and sound timers if sufficient time has passed
        since the last time that happened.
        :return:
        """
        #
        tnow = time.time()
        if tnow - self._time_at_last_dec > self.TIMER_DEC_TIMESTEP_S:
            self._time_at_last_dec = tnow
            self.ST = max(0, self.ST - 1)
            self.DT = max(0, self.DT - 1)

    def run_instruction(self, instr):
        """
        Run the two-byte instruction instr
        """
        nibs = [(instr[0] & 0xF0) >> 4,
                instr[0] & 0x0F,
                (instr[1] & 0xF0) >> 4,
                instr[1] & 0x0F]

        #print(instr.hex(), nibs)
        instr_i = int(instr[0] * 256 + instr[1])

        increment_pc = True


        if instr_i == 0x00E0:
            # 00e0
            # CLS
            self.clear_screen()
        elif instr_i == 0x00EE:
            # 00ee
            # RET
            self.ret()
        elif nibs[0] == 0:
            # 0nnn
            # SYS addr
            pass
        elif nibs[0] == 1:
            # 1nnn
            # JP addr
            # addr is 12-bit
            self.jump(address=instr_i & 0x0FFF)
            increment_pc = False
        elif nibs[0] == 2:
            # 2nnn
            # CALL addr
            self.call(address=instr_i & 0x0FFF)
            increment_pc = False
        elif nibs[0] == 3:
            # 3xbb
            # SE Vx, byte
            self.skip_if_equalv(register=nibs[1], value=instr[1])
        elif nibs[0] == 4:
            # 4xbb
            # SNE Vx, byte
            self.skip_if_not_equalv(register=nibs[1], value=instr[1])
        elif nibs[0] == 5 and nibs[3] == 0:
            # 5xy0
            # SE Vx, Vy
            self.skip_if_equalr(register1=nibs[1], register2=nibs[2])
        elif nibs[0] == 6:
            # 6xkk
            # LD Vx, byte
            self.loadv(register=nibs[1], value=instr[1])
        elif nibs[0] == 7:
            # 7xkk
            # ADD Vx, byte
            self.add(register=nibs[1], value=instr[1])
        elif nibs[0] == 8:
            if nibs[3] == 0:
                # 8xy0
                # LD Vx, Vy
                self.loadr(target_register=nibs[1], source_register=nibs[2])
            elif nibs[3] == 1:
                # 8xy1
                # OR Vx, Vy
                self.orr(register1=nibs[1], register2=nibs[2])
            elif nibs[3] == 2:
                # 8xy2
                # AND Vx, Vy
                self.andr(register1=nibs[1], register2=nibs[2])
            elif nibs[3] == 3:
                # 8xy3
                # XOR Vx, Vy
                self.xorr(register1=nibs[1], register2=nibs[2])
            elif nibs[3] == 4:
                # 8xy4
                # ADD Vx, Vy
                self.addr(register1=nibs[1], register2=nibs[2])
            elif nibs[3] == 5:
                # 8xy5
                # SUB Vx, Vy
                self.subr(register1=nibs[1], register2=nibs[2])
            elif nibs[3] == 6:
                # 8xy6
                # SHR Vx, {Vy}
                self.shift_rightr(register=nibs[1])
            elif nibs[3] == 7:
                # 8xy7
                # SUBN Vx, Vy
                self.subnr(register1=nibs[1], register2=nibs[2])
            elif nibs[3] == 0xE:
                # 8xyE
                # SHL Vx, {Vy}
                self.shift_leftr(register=nibs[1])
        elif nibs[0] == 9 and nibs[3] == 0:
            # 9xy0
            # SNE Vx, Vy
            self.skip_if_not_equalr(register1=nibs[1], register2=nibs[2])
        elif nibs[0] == 0xA:
            # Annn
            # LD I, addr
            self.load_memory_register(address=instr_i & 0x0FFF)
        elif nibs[0] == 0xB:
            # Bnnn
            # JP V0, addr
            self.jump_add(address=instr_i & 0x0FFF)
        elif nibs[0] == 0xC:
            # Cxkk
            # RND Vx, byte
            self.rnd_and(register=nibs[1], value=instr[1])
        elif nibs[0] == 0xD:
            # Dxyn
            # DRW Vx, Vy, size
            self.draw_sprite(register1=nibs[1], register2=nibs[2], sprite_size=nibs[3])
        elif nibs[0] == 0xE and instr[1] == 0x9E:
            # Ex9E
            # SKP Vx
            self.skip_if_key_pressed(key_register=nibs[1])
        elif nibs[0] == 0xE and instr[1] == 0xA1:
            # ExA1
            # SKNP Vx
            self.skip_if_key_not_pressed(key_register=nibs[1])
        elif nibs[0] == 0xF:
            if instr[1] == 0x07:
                # Fx07
                # LD Vx, DT
                self.read_delay_timer(register=nibs[1])
            elif instr[1] == 0x0A:
                # Fx0A
                # LD Vx, K
                self.wait_and_load_key(register=nibs[1])
            elif instr[1] == 0x15:
                # Fx15
                # LD DT, Vx
                self.set_delay_timer(register=nibs[1])
            elif instr[1] == 0x18:
                # Fx18
                # LD ST, Vx
                self.set_sound_timer(register=nibs[1])
            elif instr[1] == 0x1E:
                # Fx1E
                # ADD I, Vx
                self.add_to_I(register=nibs[1])
            elif instr[1] == 0x29:
                # Fx29
                # LD F, Vx
                self.set_I_to_digit_sprite(register=nibs[1])
            elif instr[1] == 0x33:
                # Fx33
                # LD B, Vx
                self.set_mem_to_bcd(register=nibs[1])
            elif instr[1] == 0x55:
                # Fx55
                # LD [I], Vx
                self.store_to_mem(register_to=nibs[1])
            elif instr[1] == 0x65:
                # Fx0A
                # LD Vx, [I]
                self.read_mem(register_to=nibs[1])
        else:
            # do nothing - illegal instruction
            print("Illegal instruction: {}".format(instr.hex()))

        return increment_pc

    def clear_screen(self):
        """
        Clear screen
        Instruction: CLS
        Bytecode: 0x00EE
        """
        self.screen.clear()

    def ret(self):
        """
        return from a subroutine (to the address at the top of the stack)
        Instruction:  RET
        Bytecode: 0x00EE
        """
        addr = self._pop_stack()
        self.PC = addr

    def jump(self, address):
        """
        jump to an address
        Instruction:  JMP nnn
        Bytecode: 0x1nnn
        """
        self.PC = address

    def _push_stack(self, value):
        """
        Helper function to push a value to the stack
        :param value: 16-bit value to push to the stack
        :return:
        """
        self.stack[self.SP] = value
        self.SP += 1
        if self.SP >= self.STACK_DEPTH:
            raise Exception("Stack Overflow")

    def _pop_stack(self):
        """
        Helper function to pop a value from the stack
        :return: value (16-bit) at the top of the stack
        """
        if self.SP == 0:
            raise Exception("Stack Empty (attempted pop)")
        self.SP -= 1
        return self.stack[self.SP]

    def call(self, address):
        """
        call a subroutine (pushes current address to the stack)
        Instruction:  CALL nnn
        Bytecode: 0x2nnn
        """
        self._push_stack(self.PC)
        self.PC = address

    def skip_if_equalv(self, register, value):
        """
        skip if the value in V[register] is equal to value
        Instruction:  SE Vx, byte
        Bytecode: 0x3xkk
        """
        if self.V[register] == value:
            self.PC += 2

    def skip_if_not_equalv(self, register, value):
        """
        skip if the value in V[register] is not equal to value
        Instruction:  SNE Vx, byte
        Bytecode: 0x4xkk
        """
        if self.V[register] != value:
            self.PC += 2

    def skip_if_equalr(self, register1, register2):
        """
        skip if the value in V[register1] is equal to value in V[register2]
        Instruction:  SE Vx, Vy
        Bytecode: 0x5xy0
        """
        if self.V[register1] == self.V[register2]:
            self.PC += 2

    def loadv(self, register, value):
        """
        load value into V[register]
        Instruction:  LD Vx, byte
        Bytecode: 0x6xkk
        """
        self.V[register] = value

    def add(self, register, value):
        """
        add value to value in V[register]
        Instruction:  ADD Vx, byte
        Bytecode: 0x7xkk
        """
        self.V[register] = (self.V[register] + value) % self.TO_8BIT

    def loadr(self, target_register, source_register):
        """
        copy value in V[source_register] into V[target_register]
        Instruction:  LD Vx, Vy
        Bytecode: 0x8xy0
        """
        self.V[target_register] = self.V[source_register]

    def orr(self, register1, register2):
        """
        bitwise or value in V[register1] with that in V[register2]; result
        is stored in V[register1]
        Instruction:  OR Vx, Vy
        Bytecode: 0x8xy1
        """
        self.V[register1] = self.V[register1] | self.V[register2]

    def andr(self, register1, register2):
        """
        bitwise and value in V[register1] with that in V[register2]; result
        is stored in V[register1]
        Instruction:  AND Vx, Vy
        Bytecode: 0x8xy2
        """
        self.V[register1] = self.V[register1] & self.V[register2]

    def xorr(self, register1, register2):
        """
        bitwise xor value in V[register1] with that in V[register2]; result
        is stored in V[register1]
        Instruction:  XOR Vx, Vy
        Bytecode: 0x8xy3
        """
        self.V[register1] = self.V[register1] ^ self.V[register2]

    def addr(self, register1, register2):
        """
        add value in V[register1] to that in V[register2]; result
        is stored in V[register1].  VF is set to carry value
        Instruction:  ADD Vx, byte
        Bytecode: 0x8xy4
        """
        # set VF to carry value
        self.V[0xF] = int(self.V[register1]) + int(self.V[register2]) > 255
        self.V[register1] = (self.V[register1] + self.V[register2]) % self.TO_8BIT

    def subr(self, register1, register2):
        """
        V[register1] := V[register1] - V[register2]
        VF is set to NOT borrow (i.e. VF := 1 if V[register1] > V[register2]
        Instruction:  ADD Vx, byte
        Bytecode: 0x8xy4
        """
        # set VF to not borrow
        self.V[0xF] = self.V[register1] > self.V[register2]
        self.V[register1] = (self.V[register1] - self.V[register2]) % self.TO_8BIT

    def shift_rightr(self, register):
        """
        Shift right (divide by two).  If the least significant bit is 1, set VF to 1
        Instruction:  SHR Vx, {Vy}
        Bytecode: 0x8xy6
        """
        self.V[0xF] = self.V[register] & 0x01
        self.V[register] >>= 1

    def subnr(self, register1, register2):
        """
        Subtract Vx from Vy, put result in Vx, i.e. Vx := Vy - Vx
        VF is set to NOT borrow
        Instruction:  SUBN Vx, Vy
        Bytecode: 0x8xy7
        """
        self.V[0xF] = self.V[register2] > self.V[register1]
        self.V[register1] = (self.V[register2] - self.V[register1]) % self.TO_8BIT

    def shift_leftr(self, register):
        """
        shift left (multiply by 2).  If the most significant bit of Vx is 1, set VF to 1
        Instruction:  SHL Vx, {Vy}
        Bytecode: 0x8xyE
        """
        self.V[0xF] = self.V[register] >= 128
        self.V[register] = (self.V[register] << 1) % self.TO_8BIT

    def skip_if_not_equalr(self, register1, register2):
        """
        skip (increment PC by 2) if Vx != Vy
        Instruction:  SHL Vx, {Vy}
        Bytecode: 0x8xyE
        """
        if self.V[register1] != self.V[register2]:
            self.PC += 2

    def load_memory_register(self, address):
        """
        put the given address into the memory register (I)
        Instruction:  LD I, nnn
        Bytecode: 0xAnnn
        """
        self.I = address % self.TO_12BIT

    def jump_add(self, address):
        """
        jump to address + V[0]
        Instruction:  JMP V0, addr
        Bytecode: 0xBnnn
        """
        self.PC = address + self.V[0]

    def rnd_and(self, register, value):
        """
        generate an 8 bit random number, then and with value and put into Vx
        Instruction:  JMP V0, addr
        Bytecode: 0xCxkk
        """
        self.V[register] = random.randrange(0, self.TO_8BIT) & value

    def draw_sprite(self, register1, register2, sprite_size):
        """
        draw the sprite_size sprite that starts at memory location I at screen location (x, y) = (Vx, Vy)
        sets VF to 1 if there is a collision.  Sprites are XORed into the screen
        Instruction:  JMP V0, addr
        Bytecode: 0xDxyn
        """
        x_st = self.V[register1]
        y_st = self.V[register2]
        collision = False
        for j in range(sprite_size):
            ram_ix = self.I + j   # eight bits per byte = 8 pixels per line as sprites are 8px wide
            for i in range(self.SPRITE_WIDTH):
                v = self.ram[ram_ix] & (1 << (7 - i)) > 0
                if (self.screen.get(x_st + i, y_st + j) & v) > 0:
                    collision = True
                self.screen.set(x=x_st + i,
                                y=y_st + j,
                                v=(self.screen.get(x_st + i, y_st + j) ^ v)
                                )
        self.V[0xF] = int(collision)

    def skip_if_key_pressed(self, key_register):
        """
        skip next instruction if the key V[key_register] is pressed
        Instruction: SKP Vx
        Bytecode: Ex9E
        """
        if self.keyboard.is_pressed(self.V[key_register]):
            self.PC += 2

    def skip_if_key_not_pressed(self, key_register):
        """
        skip next instruction if the key V[key_register] is not pressed
        Instruction: SKNP Vx
        Bytecode: ExA1
        """
        if not self.keyboard.is_pressed(self.V[key_register]):
            self.PC += 2

    def read_delay_timer(self, register):
        """
        load the value in the delay timer into register Vx
        Instruction:  LD Vx, DT
        Bytecode: 0xFx07
        """
        self.V[register] = self.DT

    def wait_and_load_key(self, register):
        """
        wait for a key press, then, once a key is pressed, load its value into V[register]
        Instruction:  LD Vx, K
        Bytecode: 0xFx0A
        """
        self.V[register] = self.keyboard.wait_for_key(callbacks=[self._update_delay_timers])

    def set_delay_timer(self, register):
        """
        set the delay timer from register Vx
        Instruction:  LD DT, Vx
        Bytecode: 0xFx15
        """
        self.DT = self.V[register]

    def set_sound_timer(self, register):
        """
        set the sound timer from register Vx
        Instruction:  LD ST, Vx
        Bytecode: 0xFx18
        """
        self.ST = self.V[register]

    def add_to_I(self, register):
        """
        add Vx to I and put the value into I
        Instruction:  ADD I, Vx
        Bytecode: 0xFx1E
        """
        self.I += self.V[register]

    def set_I_to_digit_sprite(self, register):
        """
        set the value of I to the location of the sprite for the alphanumeric character V[register]
        Instruction:  LD F, Vx
        Bytecode: 0xFx29
        """
        self.I = self.FONT_CHAR_HEIGHT * self.V[register]

    def set_mem_to_bcd(self, register):
        """
        store a bcd representation of Vx into memory at I, I+1 and I+2 (ugh!)
        Instruction:  LD B, Vx
        Bytecode: 0xFx33
        """
        self.ram[self.I] = int(self.V[register] / 100)
        self.ram[self.I + 1] = int((self.V[register] % 100) / 10)
        self.ram[self.I + 2] = int((self.V[register] % 10))

    def store_to_mem(self, register_to):
        """
        store the set of registers V0 through Vx in memory starting at location I
        Instruction:  LD [I], Vx
        Bytecode: 0xFx55
        """
        for i in range(register_to + 1):
            self.ram[self.I + i] = self.V[i]

    def read_mem(self, register_to):
        """
        read the memory from I to I + x and put it into registers V0 to Vx
        Instruction:  LD Vx, [I]
        Bytecode: 0xFx65
        """
        #if register_to > 16:
        #    raise OverflowError("Requested too many registers: {} > 16".format(self.V[register]))

        #if self.I + register_to >= self.RAM_SIZE_BYTES:
        #    raise OverflowError("Memory out of range: {} - {}".format(self.I, self.I + self.V[register]))
        for i in range(register_to + 1):
            self.V[i] = self.ram[self.I + i]

