import re

# -------------------------
# Expresión regular para instrucciones tipo I
# -------------------------
I_TYPE_RE = re.compile(
    r'^\s*(addi|xori|ori|andi|slli|srli|srai|slti|sltiu)\s+'
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+|\w+)\s*$'
)
# Nota: en el inmediato ahora también aceptamos labels (\w+)

# -------------------------
# Diccionario de instrucciones tipo I
# -------------------------
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

# -------------------------
# Utilidades
# -------------------------
def to_binary(val: int, bits: int) -> str:
    """Convierte un valor a binario con signo de longitud fija (2's complement)."""
    if val < 0:
        val = (1 << bits) + val
    return format(val & ((1 << bits) - 1), f"0{bits}b")

def assemble_i_type(mnemonic, rd, rs1, imm, symbol_table):
    info = I_TYPE_INFO[mnemonic]

    rd_bin = to_binary(int(rd), 5)
    rs1_bin = to_binary(int(rs1), 5)

    # Si el inmediato es un label, resolverlo
    if isinstance(imm, str) and not imm.startswith(("0x", "-")) and not imm.isdigit():
        if imm not in symbol_table:
            raise ValueError(f"Etiqueta no definida: {imm}")
        imm_val = symbol_table[imm] // 4  # Ejemplo simple: dirección a palabra
    else:
        imm_val = int(imm, 0)  # acepta decimal o hex

    if mnemonic in ("slli", "srli", "srai"):
        shamt = imm_val
        funct7 = info["funct7"]
        funct3 = info["funct3"]
        opcode = info["opcode"]
        imm_bin = to_binary(shamt, 5)  # shamt es 5 bits
        machine_bin = f"{funct7}{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
    else:
        imm_bin = to_binary(imm_val, 12)
        funct3 = info["funct3"]
        opcode = info["opcode"]
        machine_bin = f"{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"

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

        # Caso: label + instrucción en la misma línea
        if ":" in linea:
            parts = linea.split(":", 1)
            label = parts[0].strip()
            if label in symbol_table:
                raise ValueError(f"[Línea {num_linea}] Label duplicado: {label}")
            symbol_table[label] = location_counter
            linea = parts[1].strip()
            if not linea:
                continue  # solo era un label

        # Instrucción tipo I
        m = I_TYPE_RE.match(linea)
        if m:
            mnemonic, rd, rs1, imm = m.groups()
            instructions.append((num_linea, linea, mnemonic, rd, rs1, imm))
            location_counter += 4
        else:
            print(f"[Línea {num_linea}] ❌ Instrucción inválida: {linea}")

    return symbol_table, instructions

# -------------------------
# Segunda pasada
# -------------------------
def second_pass(instructions, symbol_table, bin_file, hex_file):
    bin_lines = []
    hex_lines = []

    for num_linea, linea, mnemonic, rd, rs1, imm in instructions:
        try:
            binario, hexa = assemble_i_type(mnemonic, rd, rs1, imm, symbol_table)
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
    asm_file = "program.asm"
    bin_file = "program.bin"
    hex_file = "program.hex"

    try:
        with open(asm_file, "r") as f:
            lines = f.readlines()

        # Primera pasada
        symbol_table, instructions = first_pass(lines)
        print("\n📌 Tabla de símbolos:", symbol_table)

        # Segunda pasada
        second_pass(instructions, symbol_table, bin_file, hex_file)

    except FileNotFoundError:
        print(f"⚠️ No se encontró el archivo {asm_file}.")

if __name__ == "__main__":
    main()
