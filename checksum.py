# reads in the save file as bytes
with open('DWM.sav', 'rb') as file:
    save = list(file.read(8192))

#setting the default values for the registers
a = 0x0A
f = 0x00
d = 0x46
e = 0x38
carry = 256

for i in range(2, 8192):
    # 1 - LOAD SRAM TO A
    a = save[i]
    # 2 - ADD E TO A. If over 255, F becomes a carry flag
    a += e
    if len(hex(a)) == 5:
        a -= carry
        f += 1
    # 3 - LOAD A INTO E
    e = a
    # 4 - LOAD $00 TO A
    a = 0x00
    # 5 - ADD D AND CARRY TO A
    a += d
    if f != 0:
        a += f
        f = 0x00
    if len(hex(a)) == 5:
        a -= carry
    # 6 - LOAD A INTO D
    d = a

# prints out what the checksum should be for the first two bytes
print("E: " + hex(e)) # byte one
print("D: " + hex(d)) # byte two
