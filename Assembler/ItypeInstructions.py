import re

# -------------------------
# Expresiones regulares para instrucciones tipo I y tipo S
# -------------------------
I_TYPE_RE = re.compile(
    # LOADS → formato: lb rd, imm(rs1)
    r'^\s*(lb|lh|lw|lbu|lhu)\s+'
    r'x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\s*\(\s*x(\d+)\s*\)\s*$'
    # ALU inmediatos → formato: addi rd, rs1, imm
    r'|^\s*(addi|xori|ori|andi|slli|srli|srai|slti|sltiu)\s+'
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\s*$'
)

S_TYPE_RE = re.compile(
    r'^\s*(sb|sh|sw)\s+'
    r'x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\(x(\d+)\)\s*$'
)

# -------------------------
# Diccionario de instrucciones tipo I
# -------------------------
I_TYPE_INFO = {
    # Aritméticas / Lógicas inmediatas
    "addi":  {"opcode": "0010011", "funct3": "000"},
    "slti":  {"opcode": "0010011", "funct3": "010"},
    "sltiu": {"opcode": "0010011", "funct3": "011"},
    "xori":  {"opcode": "0010011", "funct3": "100"},
    "ori":   {"opcode": "0010011", "funct3": "110"},
    "andi":  {"opcode": "0010011", "funct3": "111"},

    # Shifts inmediatos
    "slli":  {"opcode": "0010011", "funct3": "001", "funct7": "0000000"},
    "srli":  {"opcode": "0010011", "funct3": "101", "funct7": "0000000"},
    "srai":  {"opcode": "0010011", "funct3": "101", "funct7": "0100000"},

    # Loads
    "lb":    {"opcode": "0000011", "funct3": "000"},
    "lh":    {"opcode": "0000011", "funct3": "001"},
    "lw":    {"opcode": "0000011", "funct3": "010"},
    "lbu":   {"opcode": "0000011", "funct3": "100"},
    "lhu":   {"opcode": "0000011", "funct3": "101"},
}

# -------------------------
# Diccionario de instrucciones tipo S
# -------------------------
S_TYPE_INFO = {
    "sb": {"opcode": "0100011", "funct3": "000"},
    "sh": {"opcode": "0100011", "funct3": "001"},
    "sw": {"opcode": "0100011", "funct3": "010"},
}

# -------------------------
# Utilidades
# -------------------------
def to_binary(val: int, bits: int) -> str:
    """Convierte un valor a binario con signo (2's complement) de longitud fija."""
    if val < 0:
        val = (1 << bits) + val
    return format(val & ((1 << bits) - 1), f"0{bits}b")

def parse_immediate(imm, symbol_table=None):
    """Convierte un inmediato (decimal, hex o label) a entero."""
    if isinstance(imm, str) and not imm.startswith(("0x", "-")) and not imm.isdigit():
        if symbol_table is None or imm not in symbol_table:
            raise ValueError(f"Etiqueta no definida: {imm}")
        return symbol_table[imm]
    return int(imm, 0)

# -------------------------
# Ensamblador tipo I
# -------------------------
def assemble_i_type(mnemonic, args, symbol_table):
    info = I_TYPE_INFO[mnemonic]

    if mnemonic in ("lb", "lh", "lw", "lbu", "lhu"):
        # Formato LOAD: rd, imm(rs1)
        rd, imm, rs1 = args
        rd_bin = to_binary(int(rd), 5)
        rs1_bin = to_binary(int(rs1), 5)

        imm_val = parse_immediate(imm, symbol_table)
        imm_bin = to_binary(imm_val, 12)

        funct3 = info["funct3"]
        opcode = info["opcode"]

        machine_bin = f"{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"

    elif mnemonic in ("slli", "srli", "srai"):
        # Formato SHIFT: rd, rs1, shamt
        rd, rs1, imm = args
        rd_bin = to_binary(int(rd), 5)
        rs1_bin = to_binary(int(rs1), 5)
        shamt = int(imm, 0)

        funct7 = info["funct7"]
        funct3 = info["funct3"]
        opcode = info["opcode"]
        shamt_bin = to_binary(shamt, 5)

        machine_bin = f"{funct7}{shamt_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"

    else:
        # Formato ALU: rd, rs1, imm
        rd, rs1, imm = args
        rd_bin = to_binary(int(rd), 5)
        rs1_bin = to_binary(int(rs1), 5)

        imm_val = parse_immediate(imm, symbol_table)
        imm_bin = to_binary(imm_val, 12)

        funct3 = info["funct3"]
        opcode = info["opcode"]

        machine_bin = f"{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"

    machine_hex = f"0x{int(machine_bin, 2):08X}"
    return machine_bin, machine_hex

# -------------------------
# Ensamblador tipo S
# -------------------------
def assemble_s_type(mnemonic, args, symbol_table):
    info = S_TYPE_INFO[mnemonic]

    rs2, imm, rs1 = args
    rs1_bin = to_binary(int(rs1), 5)
    rs2_bin = to_binary(int(rs2), 5)

    imm_val = parse_immediate(imm, symbol_table)
    imm_bin = to_binary(imm_val, 12)

    imm_high = imm_bin[:7]   # bits [11:5]
    imm_low = imm_bin[7:]    # bits [4:0]

    funct3 = info["funct3"]
    opcode = info["opcode"]

    machine_bin = f"{imm_high}{rs2_bin}{rs1_bin}{funct3}{imm_low}{opcode}"
    machine_hex = f"0x{int(machine_bin, 2):08X}"
    return machine_bin, machine_hex

# -------------------------
# Primera pasada
# -------------------------
def first_pass(lines):
    symbol_table = {}
    instructions = []
    location_counter = 0

    for num_linea, linea in enumerate(lines, start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue

        # Labels
        if ":" in linea:
            parts = linea.split(":", 1)
            label = parts[0].strip()
            if label in symbol_table:
                raise ValueError(f"[Línea {num_linea}] Label duplicado: {label}")
            symbol_table[label] = location_counter
            linea = parts[1].strip()
            if not linea:
                continue

        # Instrucción tipo I
        m = I_TYPE_RE.match(linea)
        if m:
            if m.group(1):  # loads
                mnemonic, rd, imm, rs1 = m.group(1, 2, 3, 4)
                instructions.append((num_linea, linea, mnemonic, (rd, imm, rs1), "I"))
            else:  # alu
                mnemonic, rd, rs1, imm = m.group(5, 6, 7, 8)
                instructions.append((num_linea, linea, mnemonic, (rd, rs1, imm), "I"))
            location_counter += 4
            continue

        # Instrucción tipo S
        m = S_TYPE_RE.match(linea)
        if m:
            mnemonic, rs2, imm, rs1 = m.groups()
            instructions.append((num_linea, linea, mnemonic, (rs2, imm, rs1), "S"))
            location_counter += 4
            continue

        print(f"[Línea {num_linea}] ❌ Instrucción inválida: {linea}")

    return symbol_table, instructions

# -------------------------
# Segunda pasada
# -------------------------
def second_pass(instructions, symbol_table, bin_file, hex_file):
    bin_lines = []
    hex_lines = []

    for num_linea, linea, mnemonic, args, tipo in instructions:
        try:
            if tipo == "I":
                binario, hexa = assemble_i_type(mnemonic, args, symbol_table)
            elif tipo == "S":
                binario, hexa = assemble_s_type(mnemonic, args, symbol_table)
            else:
                raise ValueError("Tipo de instrucción desconocido")

            print(f"[Línea {num_linea}] {linea}")
            print(f"   Bin: {binario}")
            print(f"   Hex: {hexa}")
            bin_lines.append(binario)
            hex_lines.append(hexa)
        except Exception as e:
            print(f"[Línea {num_linea}] ⚠️ Error: {e}")

    with open(bin_file, "w") as fb:
        fb.write("\n".join(bin_lines))

    with open(hex_file, "w") as fh:
        fh.write("\n".join(hex_lines))

    print(f"\n✅ Ensamblado completado → {bin_file}, {hex_file}")

# -------------------------
# Main
# -------------------------
def main():
    asm_file = "Assembler/program.asm"
    bin_file = "program.bin"
    hex_file = "program.hex"

    try:
        with open(asm_file, "r") as f:
            lines = f.readlines()

        symbol_table, instructions = first_pass(lines)
        print("\n📌 Tabla de símbolos:", symbol_table)

        second_pass(instructions, symbol_table, bin_file, hex_file)

    except FileNotFoundError:
        print(f"⚠️ No se encontró el archivo {asm_file}.")

if __name__ == "__main__":
    main()
