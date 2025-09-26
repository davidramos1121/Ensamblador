import re
import sys


I_TYPE_RE = re.compile(
    # LOADS → formato: lb rd, imm(rs1)
    r'^\s*(lb|lh|lw|lbu|lhu)\s+'
    r'x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\s*\(\s*x(\d+)\s*\)\s*$'
    # ALU inmediatos → formato: addi rd, rs1, imm
    r'|^\s*(addi|xori|ori|andi|slli|srli|srai|slti|sltiu|jalr)\s+'
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\s*$'
)

PSEUDO_RE = re.compile(
    r'^\s*(nop|mv|not|neg|seqz|snez|sltz|sgtz|'
    r'beqz|bnez|blez|bgez|bltz|bgtz|'
    r'bgt|ble|bgtu|bleu|'
    r'j|jal|jr|jalr|ret)'
    r'(?:\s+x(\d+))?(?:\s*,\s*x(\d+))?(?:\s*,\s*(\w+|[-]?\d+|0x[0-9A-Fa-f]+))?\s*$'
)

S_TYPE_RE = re.compile(
    r'^\s*(sb|sh|sw)\s+'
    r'x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\(x(\d+)\)\s*$'
)

R_TYPE_RE = re.compile(
    r'^\s*(add|sub|xor|or|and|sll|srl|sra|slt|sltu)\s+'
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*x(\d+)\s*$'
)

B_TYPE_RE = re.compile(
    r'^\s*(beq|bne|blt|bge|bltu|bgeu)\s+'
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*(\w+)\s*$'
)

J_TYPE_RE = re.compile(
    r'^\s*(jal)\s+x(\d+)\s*,\s*(\w+|[-]?\d+|0x[0-9A-Fa-f]+)\s*$'
)

U_TYPE_RE = re.compile(
    r'^\s*(lui|auipc)\s+x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+)\s*$'
)

SYS_TYPE_RE = re.compile(
    r'^\s*(ecall|ebreak)\s*$'
)

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

    "lb":    {"opcode": "0000011", "funct3": "000"},
    "lh":    {"opcode": "0000011", "funct3": "001"},
    "lw":    {"opcode": "0000011", "funct3": "010"},
    "lbu":   {"opcode": "0000011", "funct3": "100"},
    "lhu":   {"opcode": "0000011", "funct3": "101"},

    # Jumps indirectos
    "jalr":  {"opcode": "1100111", "funct3": "000"},
}

S_TYPE_INFO = {
    "sb": {"opcode": "0100011", "funct3": "000"},
    "sh": {"opcode": "0100011", "funct3": "001"},
    "sw": {"opcode": "0100011", "funct3": "010"},
}

R_TYPE_INFO = {
    "add":  {"opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "xor":  {"opcode": "0110011", "funct3": "100", "funct7": "0000000"},
    "or":   {"opcode": "0110011", "funct3": "110", "funct7": "0000000"},
    "and":  {"opcode": "0110011", "funct3": "111", "funct7": "0000000"},
    "sll":  {"opcode": "0110011", "funct3": "001", "funct7": "0000000"},
    "srl":  {"opcode": "0110011", "funct3": "101", "funct7": "0000000"},
    "sra":  {"opcode": "0110011", "funct3": "101", "funct7": "0100000"},
    "slt":  {"opcode": "0110011", "funct3": "010", "funct7": "0000000"},
    "sltu": {"opcode": "0110011", "funct3": "011", "funct7": "0000000"},
}

B_TYPE_INFO = {
    "beq":  {"opcode": "1100011", "funct3": "000"},
    "bne":  {"opcode": "1100011", "funct3": "001"},
    "blt":  {"opcode": "1100011", "funct3": "100"},
    "bge":  {"opcode": "1100011", "funct3": "101"},
    "bltu": {"opcode": "1100011", "funct3": "110"},
    "bgeu": {"opcode": "1100011", "funct3": "111"},
}

J_TYPE_INFO = {
    "jal": {"opcode": "1101111"},
}

U_TYPE_INFO = {
    "lui":   {"opcode": "0110111"},
    "auipc": {"opcode": "0010111"},
}

SYS_TYPE_INFO = {
    "ecall":  {"opcode": "1110011", "funct3": "000", "imm": "000000000000"},
    "ebreak": {"opcode": "1110011", "funct3": "000", "imm": "000000000001"},
}

PSEUDO_INFO = {
    "nop":   {"expansion": "addi x0, x0, 0"},
    "mv":    {"expansion": "addi {rd}, {rs}, 0"},
    "not":   {"expansion": "xori {rd}, {rs}, -1"},
    "neg":   {"expansion": "sub {rd}, x0, {rs}"},
    "seqz":  {"expansion": "sltiu {rd}, {rs}, 1"},
    "snez":  {"expansion": "sltu {rd}, x0, {rs}"},
    "sltz":  {"expansion": "slt {rd}, {rs}, x0"},
    "sgtz":  {"expansion": "slt {rd}, x0, {rs}"},
    "beqz":  {"expansion": "beq {rs}, x0, {offset}"},
    "bnez":  {"expansion": "bne {rs}, x0, {offset}"},
    "blez":  {"expansion": "bge x0, {rs}, {offset}"},
    "bgez":  {"expansion": "bge {rs}, x0, {offset}"},
    "bltz":  {"expansion": "blt {rs}, x0, {offset}"},
    "bgtz":  {"expansion": "blt x0, {rs}, {offset}"},
    "bgt":   {"expansion": "blt {rt}, {rs}, {offset}"},
    "ble":   {"expansion": "bge {rt}, {rs}, {offset}"},
    "bgtu":  {"expansion": "bltu {rt}, {rs}, {offset}"},
    "bleu":  {"expansion": "bgeu {rt}, {rs}, {offset}"},
    "j":     {"expansion": "jal x0, {offset}"},
    "jr":    {"expansion": "jalr x0, {rs}, 0"},
    "ret":   {"expansion": "jalr x0, x1, 0"},
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

def assemble_r_type(mnemonic, args, symbol_table):
    info = R_TYPE_INFO[mnemonic]
    rd, rs1, rs2 = args
    rd_bin = to_binary(int(rd), 5)
    rs1_bin = to_binary(int(rs1), 5)
    rs2_bin = to_binary(int(rs2), 5)
    funct3 = info["funct3"]
    funct7 = info["funct7"]
    opcode = info["opcode"]
    machine_bin = f"{funct7}{rs2_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
    machine_hex = f"0x{int(machine_bin, 2):08X}"
    return machine_bin, machine_hex

def assemble_b_type(mnemonic, args, symbol_table):
    info = B_TYPE_INFO[mnemonic]
    rs1, rs2, label = args
    rs1_bin = to_binary(int(rs1), 5)
    rs2_bin = to_binary(int(rs2), 5)
    imm_val = parse_immediate(label, symbol_table)
    imm_offset = imm_val  # aquí tendrías que calcular offset relativo (PC-relative)
    imm_bin = to_binary(imm_offset, 13)  # 12 bits + signo
    imm_12 = imm_bin[0]
    imm_10_5 = imm_bin[1:7]
    imm_4_1 = imm_bin[7:11]
    imm_11 = imm_bin[11]
    funct3 = info["funct3"]
    opcode = info["opcode"]
    machine_bin = f"{imm_12}{imm_10_5}{rs2_bin}{rs1_bin}{funct3}{imm_4_1}{imm_11}{opcode}"
    machine_hex = f"0x{int(machine_bin, 2):08X}"
    return machine_bin, machine_hex

def assemble_j_type(mnemonic, args, symbol_table):
 info = J_TYPE_INFO[mnemonic]
 rd, imm = args
 rd_bin = to_binary(int(rd), 5)
 imm_val = parse_immediate(imm, symbol_table)
 imm_bin = to_binary(imm_val, 21) # 20 bits + signo
 imm_20 = imm_bin[0]
 imm_10_1 = imm_bin[10:20]
 imm_11 = imm_bin[9]
 imm_19_12 = imm_bin[1:9]
 machine_bin = f"{imm_20}{imm_19_12}{imm_11}{imm_10_1}{rd_bin}{info['opcode']}"
 machine_hex = f"0x{int(machine_bin, 2):08X}"
 return machine_bin, machine_hex


def assemble_u_type(mnemonic, args, symbol_table):
 info = U_TYPE_INFO[mnemonic]
 rd, imm = args
 rd_bin = to_binary(int(rd), 5)
 imm_val = parse_immediate(imm, symbol_table)
 imm_bin = to_binary(imm_val, 20)
 machine_bin = f"{imm_bin}{rd_bin}{info['opcode']}"
 machine_hex = f"0x{int(machine_bin, 2):08X}"
 return machine_bin, machine_hex


def assemble_sys_type(mnemonic):
    info = SYS_TYPE_INFO[mnemonic]   # ✅ usar la tabla correcta
    imm_bin = to_binary(int(info["imm"], 2), 12)  # imm es string binaria → conviértela
    rs1_bin = "00000"
    rd_bin = "00000"
    funct3 = info["funct3"]
    opcode = info["opcode"]
    machine_bin = f"{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
    machine_hex = f"0x{int(machine_bin, 2):08X}"
    return machine_bin, machine_hex


def expand_pseudo(mnemonic, args):
    if mnemonic not in PSEUDO_INFO:
        raise ValueError(f"Pseudoinstrucción desconocida: {mnemonic}")
    expansion = PSEUDO_INFO[mnemonic]["expansion"]

    mapping = {}
    if mnemonic in ("beqz", "bnez", "blez", "bgez", "bltz", "bgtz"):
        mapping["rs"] = args[0]      # primer operando = registro
        mapping["offset"] = args[1]  # segundo operando = etiqueta
    elif mnemonic in ("bgt", "ble", "bgtu", "bleu"):
        mapping["rs"] = args[0]
        mapping["rt"] = args[1]
        mapping["offset"] = args[2]
    else:
        if "{rd}" in expansion: mapping["rd"] = args[0]
        if "{rs}" in expansion: mapping["rs"] = args[1] if len(args) > 1 else args[0]
        if "{rt}" in expansion: mapping["rt"] = args[1]
        if "{offset}" in expansion: mapping["offset"] = args[-1]

    return expansion.format(**mapping)


def first_pass(lines):
    symbol_table = {}
    instructions = []
    location_counter = 0
    data_counter = 0
    in_text = False
    in_data = False
    errors = False 

    for num_linea, linea in enumerate(lines, start=1):
        code = linea.split('#')[0].strip()
        if not code:
            continue

        # -------------------------
        # Directivas
        # -------------------------
        if code == ".data":
            print(f"[Línea {num_linea}] 📌 Directiva reconocida: .data")
            in_data = True
            in_text = False
            continue

        elif code.startswith(".word"):
            if not in_data:
                print(f"[Línea {num_linea}] ❌ Error: '.word' solo puede usarse dentro de la sección .data")
            else:
                parts = code.split()
                if len(parts) != 2 or not parts[1].isdigit():
                    print(f"[Línea {num_linea}] ❌ Error de sintaxis en '.word'. Formato esperado: .word <entero>")
                else:
                    print(f"[Línea {num_linea}] 📌 Directiva reconocida: {code}")
                    data_counter += 4
            continue

        elif code == ".text":
            print(f"[Línea {num_linea}] 📌 Directiva reconocida: .text")
            in_text = True
            in_data = False
            location_counter = 0
            continue

        # -------------------------
        # Labels
        # -------------------------
        if ":" in code:
            parts = code.split(":", 1)
            label = parts[0].strip()
            if label in symbol_table:
                print(f"[Línea {num_linea}] ❌ Error: Label duplicado '{label}'")
            else:
                addr = location_counter if in_text else data_counter
                symbol_table[label] = addr
                print(f"[Línea {num_linea}] 📌 Etiqueta reconocida: {label} -> {addr}")
            code = parts[1].strip()
            if not code:
                continue

        # -------------------------
        # Instrucciones
        # -------------------------
        tokens = code.replace(",", " ").split()
        mnemonic = tokens[0]

        # Pseudoinstrucciones
        if mnemonic in PSEUDO_INFO:
    # Guardamos la línea como pseudoinstrucción
         instructions.append((num_linea, code, mnemonic, tokens[1:], "PSEUDO"))
         location_counter += 4
         continue

        # I-Type
        m = I_TYPE_RE.match(code)
        if m:
            if m.group(1):  # load
                mnemonic, rd, imm, rs1 = m.group(1, 2, 3, 4)
                instructions.append((num_linea, code, mnemonic, (rd, imm, rs1), "I"))
            else:
                mnemonic, rd, rs1, imm = m.group(5, 6, 7, 8)
                instructions.append((num_linea, code, mnemonic, (rd, rs1, imm), "I"))
            location_counter += 4
            continue

        # S-Type
        m = S_TYPE_RE.match(code)
        if m:
            mnemonic, rs2, imm, rs1 = m.groups()
            instructions.append((num_linea, code, mnemonic, (rs2, imm, rs1), "S"))
            location_counter += 4
            continue

        # R-Type
        m = R_TYPE_RE.match(code)
        if m:
            mnemonic, rd, rs1, rs2 = m.groups()
            instructions.append((num_linea, code, mnemonic, (rd, rs1, rs2), "R"))
            location_counter += 4
            continue

        # B-Type
        m = B_TYPE_RE.match(code)
        if m:
            mnemonic, rs1, rs2, label = m.groups()
            instructions.append((num_linea, code, mnemonic, (rs1, rs2, label), "B"))
            location_counter += 4
            continue

        # J-Type (ej: jal rd, label)
        m = J_TYPE_RE.match(code)
        if m:
            mnemonic, rd, label = m.groups()
            instructions.append((num_linea, code, mnemonic, (rd, label), "J"))
            location_counter += 4
            continue

        # U-Type (ej: lui rd, imm  |  auipc rd, imm)
        m = U_TYPE_RE.match(code)
        if m:
            mnemonic, rd, imm = m.groups()
            instructions.append((num_linea, code, mnemonic, (rd, imm), "U"))
            location_counter += 4
            continue

        # System (ecall, ebreak)
        if mnemonic in ["ecall", "ebreak"]:
            instructions.append((num_linea, code, mnemonic, (), "SYS"))
            location_counter += 4
            continue

        # -------------------------
        # Si llegamos aquí → Error
        # -------------------------
        if mnemonic.startswith("."):
            print(f"[Línea {num_linea}] ❌ Error de directiva: '{mnemonic}' no es válida o está fuera de contexto")
            errors = True
        elif mnemonic not in (list(I_TYPE_INFO.keys()) +
                              list(S_TYPE_INFO.keys()) +
                              list(R_TYPE_INFO.keys()) +
                              list(B_TYPE_INFO.keys()) +
                              list(J_TYPE_INFO.keys()) +
                              list(U_TYPE_INFO.keys()) +
                              list(PSEUDO_INFO.keys()) +
                              ["ecall", "ebreak"]):
            print(f"[Línea {num_linea}] ❌ Instrucción inválida: '{mnemonic}'")
            errors = True
        elif len(tokens) == 1:
            print(f"[Línea {num_linea}] ❌ Error de operandos en '{mnemonic}'")
            errors = True
        else:
            print(f"[Línea {num_linea}] ❌ Error de sintaxis en '{code}'")
            errors = True

    if errors:
        print("\n⛔ Ensamblado detenido: se encontraron errores en la primera pasada.")
        sys.exit(1)  # <-- detenemos ejecución aquí

    return symbol_table, instructions
# -------------------------
# Segunda pasada
# -------------------------
def second_pass(instructions, symbol_table, bin_file, hex_file):
    bin_lines = []
    hex_lines = []

    for num_linea, code, mnemonic, args, tipo in instructions:
        try:
            if tipo == "I":
                binario, hexa = assemble_i_type(mnemonic, args, symbol_table)

            elif tipo == "S":
                binario, hexa = assemble_s_type(mnemonic, args, symbol_table)

            elif tipo == "R":
                binario, hexa = assemble_r_type(mnemonic, args, symbol_table)

            elif tipo == "B":
                if args[2] not in symbol_table:
                    raise ValueError(f"Etiqueta no definida: '{args[2]}'")
                binario, hexa = assemble_b_type(mnemonic, args, symbol_table)

            elif tipo == "J":
                if args[1] not in symbol_table:
                    raise ValueError(f"Etiqueta no definida: '{args[1]}'")
                binario, hexa = assemble_j_type(mnemonic, args, symbol_table)

            elif tipo == "U":
                binario, hexa = assemble_u_type(mnemonic, args, symbol_table)

            elif tipo == "SYS":
                binario, hexa = assemble_sys_type(mnemonic)

            elif tipo == "PSEUDO":
                # Expandir la pseudo (devuelve una instrucción real, e.g. "addi x1, x2, 0")
                expanded = expand_pseudo(mnemonic, args)
                print(f"[Línea {num_linea}] 🔄 Expansión pseudo: {code} → {expanded}")

                # Matchear la instrucción expandida usando las regex (usar 'expanded' sin modificar)
                m = I_TYPE_RE.match(expanded)
                if m:
                    # En I_TYPE_RE la primera alternativa (loads) produce grupo(1) no None
                    if m.group(1):
                        # load: group(1)=mnemonic, group(2)=rd, group(3)=imm, group(4)=rs1
                        mnem_real, rd, imm, rs1 = m.group(1, 2, 3, 4)
                        binario, hexa = assemble_i_type(mnem_real, (rd, imm, rs1), symbol_table)
                    else:
                        # ALU immediate: group(5)=mnemonic, group(6)=rd, group(7)=rs1, group(8)=imm
                        mnem_real, rd, rs1, imm = m.group(5, 6, 7, 8)
                        binario, hexa = assemble_i_type(mnem_real, (rd, rs1, imm), symbol_table)

                else:
                    m = R_TYPE_RE.match(expanded)
                    if m:
                        mnem_real, rd, rs1, rs2 = m.groups()
                        binario, hexa = assemble_r_type(mnem_real, (rd, rs1, rs2), symbol_table)
                    else:
                        m = S_TYPE_RE.match(expanded)
                        if m:
                            mnem_real, rs2, imm, rs1 = m.groups()
                            binario, hexa = assemble_s_type(mnem_real, (rs2, imm, rs1), symbol_table)
                        else:
                            m = B_TYPE_RE.match(expanded)
                            if m:
                                mnem_real, rs1, rs2, label = m.groups()
                                if label not in symbol_table:
                                    raise ValueError(f"Etiqueta no definida: '{label}'")
                                binario, hexa = assemble_b_type(mnem_real, (rs1, rs2, label), symbol_table)
                            else:
                                m = J_TYPE_RE.match(expanded)
                                if m:
                                    mnem_real, rd, label = m.groups()
                                    if label not in symbol_table:
                                        raise ValueError(f"Etiqueta no definida: '{label}'")
                                    binario, hexa = assemble_j_type(mnem_real, (rd, label), symbol_table)
                                else:
                                    m = U_TYPE_RE.match(expanded)
                                    if m:
                                        mnem_real, rd, imm = m.groups()
                                        binario, hexa = assemble_u_type(mnem_real, (rd, imm), symbol_table)
                                    else:
                                        # SYS-type?
                                        if SYS_TYPE_RE.match(expanded):
                                            binario, hexa = assemble_sys_type(expanded.strip())
                                        else:
                                            raise ValueError(f"No se pudo ensamblar la expansión: {expanded}")

            else:
                raise ValueError(f"Tipo de instrucción desconocido: {tipo}")

            print(f"[Línea {num_linea}] {code}")
            print(f"   Bin: {binario}")
            print(f"   Hex: {hexa}")
            bin_lines.append(binario)
            hex_lines.append(hexa)

        except Exception as e:
            print(f"[Línea {num_linea}] ❌ Error: {e}")
            print("\n⛔ Ensamblado detenido en segunda pasada.")
            sys.exit(1)

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
        sys.exit(1)


if __name__ == "__main__":
    main()
