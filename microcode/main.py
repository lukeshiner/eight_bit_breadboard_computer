"""Generate binary files for the microcode ROMs in the eight bit computer."""

from pathlib import Path

import toml

CONFIG_PATH = Path(__file__).parent / "microcode.toml"

CONTROL_WORD = "control_word"
OPCODES = "opcodes"
T_STEP_COUNT = "t_step_count"
LOAD_COMMAND = "load_command"
ROMS = "roms"
STEP_BITS = "step_bits"
OPCODE_BITS = "opcode_bits"


class Roms:
    roms = []
    step_bits = 1
    opcode_bits = 1

    @classmethod
    def load(cls, roms, step_bits, opcode_bits):
        cls.step_bits = step_bits
        cls.opcode_bits = opcode_bits
        cls.roms = [Rom(rom) for rom in roms]
        cls.name_lookup = {rom.name: rom for rom in cls.roms}

    @classmethod
    def get(cls, name):
        return cls.name_lookup[name]


class Rom:
    """Wrapper for a microcode Rom."""

    def __init__(self, name):
        self.name = name
        self.data = [0] * (2 ** (Roms.step_bits + Roms.opcode_bits))

    def filename(self):
        return f"microcode_{self.name.lower()}.bin"


class ControlLine:
    """Wrapper for a control line."""

    def __init__(self, name, abr, rom, position):
        self.name = name
        self.abr = abr
        self.rom = Roms.get(rom)
        self.position = position

    def __repr__(self):
        return f"<Control Line: {self.abr}>"

    def __str__(self):
        return self.abr


class ControlWord:
    """Container for control lines."""

    control_words = []
    abr_lookup = {}
    count = 0

    @classmethod
    def load(cls, control_words):
        """Load the control words from the config file."""
        cls.control_words = [ControlLine(**line) for line in control_words.values()]
        cls.abr_lookup = {_.abr: _ for _ in cls.control_words}
        cls.count = len(cls.control_words)

    @classmethod
    def get(cls, abr):
        """Return a ControlLine objects matching the abriviation."""
        return cls.abr_lookup[abr]

    @classmethod
    def t_steps(cls, t_steps):
        """Convert a list of lists of strings representing T steps to a list of lists of ControlLine objects."""
        steps = []
        for step in t_steps:
            lines = [ControlWord.get(control_line_abr) for control_line_abr in step]
            steps.append(TStep(*lines))
        return steps


class Opcode:
    """Wrapper for an opcode."""

    def __init__(self, name, abr, opcode, t_steps):
        self.name = name
        self.abr = abr
        self.opcode = opcode
        self.t_steps = ControlWord.t_steps(t_steps)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Opcode: {self.abr}>"


class TStep:
    def __init__(self, *control_lines):
        self.control_lines = control_lines

    def __repr__(self):
        return f"<TStep: {', '.join(_.abr for _ in self.control_lines)}>"

    def add(self, address):
        for rom in Roms.roms:
            self.add_to_rom(address, rom)

    def add_to_rom(self, address, rom):
        bits = [0] * 8
        for line in self.control_lines:
            if line.rom == rom:
                bits[line.position] = 1
        code = int("".join((str(bit) for bit in bits)), 2)
        rom.data[address] = code


class Main:
    """Create binary files for the 8-bit computer microcode ROMs."""

    def __init__(self):
        """Load config."""
        self.load_instruction_set()

    def run(self):
        """Create the binary files."""
        self.add_load_command()
        for opcode in self.opcodes:
            self.add_opcode(opcode)
        self.save_binary()

    def get_config(self):
        """Load the config from the config file."""
        with open(CONFIG_PATH) as f:
            return toml.load(f)

    def load_instruction_set(self):
        """Load instruction set information from the config file."""
        self.config = self.get_config()
        step_bits = self.config[STEP_BITS]
        opcode_bits = self.config[OPCODE_BITS]
        Roms.load(self.config[ROMS], step_bits=step_bits, opcode_bits=opcode_bits)
        ControlWord.load(self.config[CONTROL_WORD])
        self.load_comand = ControlWord.t_steps(self.config[LOAD_COMMAND])
        self.t_step_count = self.config[T_STEP_COUNT]
        self.opcodes = [Opcode(**opcode) for opcode in self.config[OPCODES].values()]

    def add_load_command(self):
        """Add the load command for all possible opcodes to the ROMs."""
        for instruction_space in range(2 ** Roms.opcode_bits):
            for i, step in enumerate(self.load_comand):
                address = (instruction_space << Roms.step_bits) + i
                step.add(address)

    def add_opcode(self, opcode):
        """Add T Steps for an opcode to the ROMs."""
        start_address = (opcode.opcode << Roms.step_bits) + len(self.load_comand)
        for i, step in enumerate(opcode.t_steps):
            step.add(start_address + i)

    def save_binary(self):
        """Save binary data for the ROMs."""
        for rom in Roms.roms:
            with open(Path(__file__).parent / rom.filename(), "wb") as f:
                f.write(bytearray(rom.data))


if __name__ == "__main__":
    Main().run()
