    .text
main:
    addi x1, x0, 4
    lui x2, 0x12345
    auipc x3, 0x10
    jal x4, target
    addi x5, x0, 7
target:
    jalr x6, x2, 8
