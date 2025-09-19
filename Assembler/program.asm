nop
mv x5, x6
not x7, x8
neg x9, x10
seqz x11, x12
snez x13, x14
sltz x15, x16
sgtz x17, x18

beqz x5, etiqueta1
bnez x6, etiqueta2
blez x7, etiqueta3
bgez x8, etiqueta4
bltz x9, etiqueta5
bgtz x10, etiqueta6

j etiqueta7
jal etiqueta8
jr x1
jalr x2
ret

addi x1, x0, 100
ori  x2, x1, 0x0F
andi x3, x2, 255
lw   x4, 0(x1)

sb x2, 0(x1)
sh x3, 4(x1)
sw x4, 8(x1)

etiqueta1: addi x20, x0, 1
etiqueta2: addi x21, x0, 2
etiqueta3: addi x22, x0, 3
etiqueta4: addi x23, x0, 4
etiqueta5: addi x24, x0, 5
etiqueta6: addi x25, x0, 6
etiqueta7: addi x26, x0, 7
etiqueta8: addi x27, x0, 8
