start:
  add x1, x2, x3
  sub x4, x5, x6
loop:
  beq x1, x2, start
  bne x1, x2, loop
  