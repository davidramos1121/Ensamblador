import re

# ==============================
# Tablas de instrucciones
# ==============================

R_TYPE_INFO = {
    'add':  ('0110011', '000', '0000000'),
    'sub':  ('0110011', '000', '0100000'),
    'xor':  ('0110011', '100', '0000000'),
    'or':   ('0110011', '110', '0000000'),
    'and':  ('0110011', '111', '0000000'),
    'sll':  ('0110011', '001', '0000000'),
    'srl':  ('0110011', '101', '0000000'),
    'sra':  ('0110011', '101', '0100000'),
    'slt':  ('0110011', '010', '0000000'),
    'sltu': ('0110011', '011', '0000000')
}

B_TYPE_INFO = {
    'beq': ('1100011', '000'),
    'bne': ('1100011', '001'),
    'blt': ('1100011', '004'),
    'bge': ('1100011', '005'),
    'bltu': ('1100011', '006'),
    'bgeu': ('1100011', '007')
}


I_TYPE_INFO = {
    "addi":  {"opcode": "0010011", "funct3": "000"},
    "slti":  {"opcode": "0010011", "funct3": "010"},
    "sltiu": {"opcode": "0010011", "funct3": "011"},
    "xori":  {"opcode": "0010011", "funct3": "100"},
    "ori":   {"opcode": "0010011", "funct3": "110"},
    "andi":  {"opcode": "0010011", "funct3": "111"},
    "slli":  {"opcode": "0010011", "funct3": "001", "funct7": "0000000"},
    "srli":  {"opcode": "0010011", "funct3": "101", "funct7": "0000000"},
    "srai":  {"opcode": "0010011", "funct3": "101", "funct7": "0100000"},
}

# ==============================
# Expresiones regulares
# ==============================

R_RE = re.compile(r'^\s*(\w+)\s+x(\d+),\s*x(\d+),\s*x(\d+)\s*$')
B_RE = re.compile(r'^\s*(\w+)\s+x(\d+),\s*x(\d+),\s*(\w+)\s*$')
I_RE = re.compile(
    r'^\s*(addi|xori|ori|andi|slli|srli|srai|slti|sltiu)\s+'
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\s*$'
)

# ==============================
# Utilidades
# ==============================

def to_bin(val: int, bits: int) -> str:
    if val < 0:
        val = (1 << bits) + val
    return format(val & ((1 << bits) - 1), f"0{bits}b")

def reg(num): 
    return to_bin(int(num), 5)

# ==============================
# Ensambladores por tipo
# ==============================

def assemble_r_type(mnemonic, rd, rs1, rs2):
    opcode, funct3, funct7 = R_TYPE_INFO[mnemonic]
    bin_inst = f"{funct7}{reg(rs2)}{reg(rs1)}{funct3}{reg(rd)}{opcode}"
    hex_inst = f"0x{int(bin_inst,2):08X}"
    return bin_inst, hex_inst

def assemble_b_type(mnemonic, rs1, rs2, label, symbol_table, pc):
    opcode, funct3 = B_TYPE_INFO[mnemonic]
    target = symbol_table[label]
    offset = target - pc
    offset //= 2  # los saltos van en múltiplos de 2 bytes

    imm = to_bin(offset, 13)
    imm_12 = imm[0]
    imm_10_5 = imm[1:7]
    imm_4_1 = imm[7:11]
    imm_11 = imm[11]

    bin_inst = f"{imm_12}{imm_10_5}{reg(rs2)}{reg(rs1)}{funct3}{imm_4_1}{imm_11}{opcode}"
    hex_inst = f"0x{int(bin_inst,2):08X}"
    return bin_inst, hex_inst

def assemble_i_type(mnemonic, rd, rs1, imm, symbol_table):
    info = I_TYPE_INFO[mnemonic]
    rs1_bin = reg(rs1)
    rd_bin = reg(rd)

    if isinstance(imm, str) and not imm.startswith(("0x","-")) and not imm.isdigit():
        imm_val = symbol_table[imm] // 4
    else:
        imm_val = int(imm, 0)

    if mnemonic in ("slli", "srli", "srai"):
        shamt = imm_val
        funct7 = info["funct7"]
        funct3 = info["funct3"]
        opcode = info["opcode"]
        imm_bin = to_bin(shamt, 5)
        bin_inst = f"{funct7}{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
    else:
        imm_bin = to_bin(imm_val, 12)
        funct3 = info["funct3"]
        opcode = info["opcode"]
        bin_inst = f"{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"

    hex_inst = f"0x{int(bin_inst,2):08X}"
    return bin_inst, hex_inst

# ==============================
# Primera pasada
# ==============================

def first_pass(lines):
    symbol_table = {}
    instructions = []
    pc = 0

    for num_linea, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        # label + instrucción
        if ":" in line:
            label, rest = line.split(":", 1)
            label = label.strip()
            if label in symbol_table:
                raise ValueError(f"[Línea {num_linea}] Label duplicado: {label}")
            symbol_table[label] = pc
            line = rest.strip()
            if not line:
                continue

        if R_RE.match(line):
            mnemonic, rd, rs1, rs2 = R_RE.match(line).groups()
            instructions.append((num_linea, "R", mnemonic, rd, rs1, rs2, pc))
            pc += 4
        elif B_RE.match(line):
            mnemonic, rs1, rs2, label = B_RE.match(line).groups()
            instructions.append((num_linea, "B", mnemonic, rs1, rs2, label, pc))
            pc += 4
        elif I_RE.match(line):
            mnemonic, rd, rs1, imm = I_RE.match(line).groups()
            instructions.append((num_linea, "I", mnemonic, rd, rs1, imm, pc))
            pc += 4
        else:
            print(f"[Línea {num_linea}] ❌ Instrucción no reconocida: {line}")

    return symbol_table, instructions

# ==============================
# Segunda pasada
# ==============================

def second_pass(instructions, symbol_table, bin_file, hex_file):
    bin_lines = []
    hex_lines = []

    for num_linea, tipo, *args in instructions:
        try:
            if tipo == "R":
                mnemonic, rd, rs1, rs2, pc = args
                bin_inst, hex_inst = assemble_r_type(mnemonic, rd, rs1, rs2)
            elif tipo == "B":
                mnemonic, rs1, rs2, label, pc = args
                bin_inst, hex_inst = assemble_b_type(mnemonic, rs1, rs2, label, symbol_table, pc)
            elif tipo == "I":
                mnemonic, rd, rs1, imm, pc = args
                bin_inst, hex_inst = assemble_i_type(mnemonic, rd, rs1, imm, symbol_table)

            print(f"[Línea {num_linea}] {tipo} → {bin_inst} ({hex_inst})")
            bin_lines.append(bin_inst)
            hex_lines.append(hex_inst)
        except Exception as e:
            print(f"[Línea {num_linea}] ⚠️ Error: {e}")

    with open(bin_file, "w") as fb:
        fb.write("\n".join(bin_lines))
    with open(hex_file, "w") as fh:
        fh.write("\n".join(hex_lines))

    print(f"\n✅ Ensamblado completado → {bin_file}, {hex_file}")

# ==============================
# Main
# ==============================

def main():
    asm_file = "Prueba_two_pass.asm"
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
