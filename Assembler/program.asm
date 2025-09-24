    nop
    mv x1, x2
    not x3, x4
    neg x5, x6
    seqz x7, x8
    snez x9, x10
    sltz x11, x12
    sgtz x13, x14

    beqz x15, label1
    bnez x16, label2
    blez x17, label3
    bgez x18, label4
    bltz x19, label5
    bgtz x20, label6

    bgt x21, x22, label7
    ble x23, x24, label8
    bgtu x25, x26, label9
    bleu x27, x28, label10

    j label11
    jr x29
    ret

label1:
    addi x1, x0, 1
label2:
    addi x2, x0, 2
label3:
    addi x3, x0, 3
label4:
    addi x4, x0, 4
label5:
    addi x5, x0, 5
label6:
    addi x6, x0, 6
label7:
    addi x7, x0, 7
label8:
    addi x8, x0, 8
label9:
    addi x9, x0, 9
label10:
    addi x10, x0, 10
label11:
    addi x11, x0, 11
