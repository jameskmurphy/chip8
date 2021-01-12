import pygame
import time
import traceback

from .cpu import CPU
from .io import PyGameKeyboard, PyGameScreen

DEFAULT_CPU_FREQUENCY_HZ = 1000
DEFAULT_IO_FREQUENCY_HZ = 60


class Chip8VM:

    def __init__(self, cpu_freq_hz=DEFAULT_CPU_FREQUENCY_HZ, io_freq_hz=DEFAULT_IO_FREQUENCY_HZ):
        self.screen = None
        self.keyboard = None
        self.cpu = None
        self.running=False
        self.cpu_freq_hz = cpu_freq_hz
        self.io_freq_hz = io_freq_hz
        pygame.init()
        self.restart()

    def restart(self):
        self.screen = PyGameScreen()
        self.keyboard = PyGameKeyboard()
        self.cpu = CPU(keyboard=self.keyboard, screen=self.screen)

    def shutdown(self):
        pygame.quit()

    def run(self):
        t_last_io = time.time()
        t_last_cpu = 0
        cpu_cycles = 0

        self.running = True
        try:
            while self.running:
                tnow = time.time()

                time.sleep(max(0, 1. / self.cpu_freq_hz - (tnow - t_last_cpu) - 0.001))

                if tnow - t_last_cpu > 1. / self.cpu_freq_hz:
                    self.cpu.tick()
                    cpu_cycles += 1
                    t_last_cpu = tnow

                if tnow - t_last_io > 1. / self.io_freq_hz:
                    # time for IO
                    fps = 1. / (time.time() - t_last_io)
                    print("cpu {:.2f}kHz  {:2.0f}fps  kb={} ".format(cpu_cycles * fps / 1000, fps, self.keyboard.key_pressed), end="\r")

                    cpu_cycles = 0

                    self.keyboard.key_reader()
                    self.screen.draw()

                    t_last_io = time.time()
                    # Did the user click the window close button?
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            pygame.quit()

        except Exception as e:
            self.cpu.print_state()
            print(e)
            traceback.print_exc()
        finally:
            pygame.quit()

    def load_rom(self, filename):
        with open(filename, "rb") as f:
            bytecode = f.read()
            self.cpu.load_program(bytecode)

    def load_program(self, bytecode):
        self.cpu.load_program(bytecode)
