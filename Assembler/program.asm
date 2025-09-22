    .data
msg: .word 1234

    .text
main:
    addi x5, x0, 10
    sw x5, 0(x1)

    adii x1, x2, 5
    addi x1, x2, x3
    addi x1, x2, 123456
    beq x1, x2, notfound
    addi x1
