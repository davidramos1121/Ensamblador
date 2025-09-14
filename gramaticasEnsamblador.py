import re

# Expresión general para instrucciones tipo I (como las de tu tabla)
I_TYPE_RE = re.compile(
    r'^\s*(addi|xori|ori|andi|slli|srli|srai|slti|sltiu)\s+'   # mnemónicos válidos
    r'x(\d+)\s*,\s*x(\d+)\s*,\s*([-]?\d+|0x[0-9A-Fa-f]+)\s*$'  # rd, rs1, inmediato
)

# Ejemplo de uso
tests = [
    "addi x1, x2, 100",
    "xori x5, x3, -12",
    "ori x10, x4, 0xFF",
    "andi x7, x7, 255",
    "slli x8, x8, 3",
    "srli x9, x9, 0x1F",
    "srai x11, x11, 4",
    "slti x12, x13, -1",
    "sltiu x14, x15, 1024",
]

for t in tests:
    m = I_TYPE_RE.match(t)
    if m:
        mnemonic, rd, rs1, imm = m.groups()
        print(f"{t} → {mnemonic}, rd={rd}, rs1={rs1}, imm={imm}")
