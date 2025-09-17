
import re

# Tabla de parámetros de instrucciones tipo R
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

# Convierte registros x0..x31 en binario de 5 bits
def reg_to_bin(reg):
    num = int(reg[1:])  # quitar la 'x'
    return format(num, '05b')

# Convierte un número binario a hexadecimal de 8 dígitos
def bin_to_hex(bin_str):
    return format(int(bin_str, 2), '08x')

# Compilar archivo de entrada a .bin y .hex
def compile_rv32i_r(input_file, bin_out, hex_out):
    pattern = re.compile(r'^\s*(\w+)\s+x(\d+),\s*x(\d+),\s*x(\d+)\s*$')

    bin_lines = []
    hex_lines = []

    with open(input_file, 'r') as f:
        for line in f:
            match = pattern.match(line)
            if not match:
                continue

            inst, rd, rs1, rs2 = match.groups()
            rd_bin = format(int(rd), '05b')
            rs1_bin = format(int(rs1), '05b')
            rs2_bin = format(int(rs2), '05b')

            if inst not in R_TYPE:
                raise ValueError(f"Instrucción no soportada: {inst}")

            opcode, funct3, funct7 = R_TYPE[inst]

            bin_inst = f"{funct7}{rs2_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
            hex_inst = bin_to_hex(bin_inst)

            bin_lines.append(bin_inst)
            hex_lines.append(hex_inst)

    with open(bin_out, 'w') as fb:
        fb.write('\n'.join(bin_lines))

    with open(hex_out, 'w') as fh:
        fh.write('\n'.join(hex_lines))

# ---- Uso ----
# Crea un archivo "programa.txt" con contenido como:
# add x1, x2, x3
# sub x4, x5, x6
# and x7, x8, x9
# Luego ejecuta:
compile_rv32i_r('programa.txt', 'salida.bin', 'salida.hex')
