
start:  addi x5, x0, 10     
        ori  x6, x5, 0xFF    

loop:   andi x7, x6, start   
        slli x8, x7, 2     
        addi x9, x8, loop    
