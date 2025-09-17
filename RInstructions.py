

import re

# --- Tablas de instrucciones ---
R_TYPE = {
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

B_TYPE = {
    'beq': ('1100011', '000'),
    'bne': ('1100011', '001')
}

def reg(num): return format(int(num), '05b')
def to_hex(b): return format(int(b, 2), '08x')

# --- Pasada 1: construir tabla de etiquetas ---
def primera_pasada(lines):
    labels = {}
    pc = 0
    for line in lines:
        clean = line.strip()
        if not clean or clean.startswith('#'):  # comentario
            continue
        if clean.endswith(':'):
            label = clean[:-1]
            labels[label] = pc
        else:
            pc += 4
    return labels

# --- Pasada 2: generar binario ---
def segunda_pasada(lines, labels):
    bin_lines = []
    hex_lines = []
    pc = 0

    # patrones regex
    r_pat = re.compile(r'^\s*(\w+)\s+x(\d+),\s*x(\d+),\s*x(\d+)\s*$')
    b_pat = re.compile(r'^\s*(\w+)\s+x(\d+),\s*x(\d+),\s*(\w+)\s*$')

    for line in lines:
        text = line.strip()
        if not text or text.startswith('#') or text.endswith(':'):
            continue

        # --- tipo R ---
        m = r_pat.match(text)
        if m:
            inst, rd, rs1, rs2 = m.groups()
            opcode, funct3, funct7 = R_TYPE[inst]
            bin_inst = f"{funct7}{reg(rs2)}{reg(rs1)}{funct3}{reg(rd)}{opcode}"
            bin_lines.append(bin_inst)
            hex_lines.append(to_hex(bin_inst))
            pc += 4
            continue

        # --- tipo B ---
        m = b_pat.match(text)
        if m:
            inst, rs1, rs2, label = m.groups()
            opcode, funct3 = B_TYPE[inst]
            imm = labels[label] - pc
            imm = imm // 2  # en instrucciones RISC-V, offset está en múltiplos de 2

            # Formato B: imm[12] | imm[10:5] | rs2 | rs1 | funct3 | imm[4:1] | imm[11] | opcode
            imm_bin = format(imm & 0x1FFF, '013b')
            imm_12 = imm_bin[0]
            imm_10_5 = imm_bin[1:7]
            imm_4_1 = imm_bin[7:11]
            imm_11 = imm_bin[11]

            bin_inst = f"{imm_12}{imm_10_5}{reg(rs2)}{reg(rs1)}{funct3}{imm_4_1}{imm_11}{opcode}"
            bin_lines.append(bin_inst)
            hex_lines.append(to_hex(bin_inst))
            pc += 4
            continue

        raise ValueError(f"Línea no reconocida: {text}")

    return bin_lines, hex_lines

def ensamblar(archivo_in, bin_out, hex_out):
    with open(archivo_in) as f:
        lines = f.readlines()

    labels = primera_pasada(lines)
    bin_lines, hex_lines = segunda_pasada(lines, labels)

    with open(bin_out, 'w') as fb: fb.write('\n'.join(bin_lines))
    with open(hex_out, 'w') as fh: fh.write('\n'.join(hex_lines))

# --- Uso ---
ensamblar('Prueba_two_pass.asm', 'program.bin', 'program.hex')

