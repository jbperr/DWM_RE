# [Save Viewer/Editor](https://www.benperry.org/dwm)
# Dragon Warrior Monsters Save Reverse Engineer

Dragon Warrior Monsters (DWM) is one of my favorite childhood video games. I would always find myself playing it over and over again. It is similar to Pokemon in its monster collecting and monster fighting game-loop. DWM allows you to tame monsters, that live behind portals called gates, and battle those monsters in a tournament with the eventual goal of saving your sister. 

This past couple years I have gotten interested in reverse engineering and trying to understand how things work. After seeing what [PKHeX](https://github.com/kwsch/PKHeX) can do with Pokemon saves, I wanted to see what I could make for DWM. The save file structure has been extensively studied and documented for every Pokemon game; whereas, for DWM there really is not much. I would have to go from the ground up. I decided to start by looking at the save file structure for [Generation 2 Pokemon](https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_%28Generation_II%29) as it would most likely be the most similar as the games were made around the same time (1998 for DWM and 1999 for Pokemon Gold/Silver). I knew that the save structures wouldn't be the exact same, but it allowed me to spot some patterns such as using a [similar structure](https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_%28Generation_II%29#Pok.C3.A9dex_owned.2C_Pok.C3.A9dex_seen) to store whether a certain Pokemon or certain monster had been captured or how the checksum is used to validate the save. To start, I just opened up the save in a hex editor to see what was going on. But hold on, what even is a Game Boy save?


## Game Boy Saves

All Game Boy games that had a save file (Pokemon Gold, Zelda: Link's Awakening, DWM) had a battery in the cartridge that kept some of the cartridge's memory on all the time so that data could be kept. This is why a lot of people recently have been turning on their old Pokemon game and finding that the save has disappeared. The battery died and with it the data too. Luckily, you can replace the batteries and you can extend the life of the data; however, in order to replace the battery, the saves will get lost as the power will be cut while the battery is disconnected. There is another way to protect your saves though. A [Sanni Cart Reader](https://github.com/sanni/cartreader) can be used to read and write saves, read game roms, and much more from GB/C/A, NES, SNES, N64, SEGA consoles, etc. In 2021, I built a modification of the Sanni reader by [makho](https://github.com/makhowastaken/cartreader) to preserve all my old Game Boy game saves. Anyways, with that basic information out of the way. I dumped my save and then opened it in a hex editor to see what was going on.

# DWM Character Encoding

`FC 77 01 00 02 00 00 03 01 00 40 18 01 80 B8 00 11 0B 18 01 B8 00 E0 01 00 01 00 00 00 00 78 00 38 00 0F 4F 01 02 00 00 00 03 C0 06 D5 CE E5 D5 00 3B 01 00 00 09 00 E8 00 48 00 02 03 11 00 00 05 80 07 14 9A 1C A7 03 07 00 00 14 9A 00 02 00 00 FF FF B4 9B 00 00 02 04 FF 00 00 00 00 00 05 FF D8 00 B8 00 00 00 00 00 00 8E CA 01 02 01 15 0C 0A 0A 04 1D 45 03 0F 00 00 F9 C5 C9 F6 67 0A`

Here are the first 128 of 8192 bytes of the the save file. At first, it is a lot to look at. But after reading the page on [Pokemon character encoding](https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_II)), I figured the first step is to figure out how the text gets stored. I did this by starting up a new save and naming myself `AAAA` so that I can then look in the save file for four bytes that repeat themself. After examining that save file, I found where your name gets stored. Here are bytes 374-384.   

 `00 00 00 00 24 24 24 24 F0` 

 You can see the byte `24` repeated four times from byte 380 to byte 383. So now we know that 'A' is represented by `24`, but what about everything else? Well we could start up a new save file and name ourselves a mix of characters and then record what gets saved as our name. However, that would take a long time compared to if we could just edit the hex and then load the save to view how the name changed. So I tried just that and changed the name bytes to `25 25 25 25`. I loaded up the save to see what happened and was greeted by the game showing me there was no save game to be loaded. This is what happens when the save is corrupted or there is no save to be loaded. This tells me the game uses some kind of checksum to determine validity of a save file. From reading how Pokemon implements a checksum, I hoped it would be some sort of simple sum across the whole file and then that data would be stored somewhere in the file. If it was just a sum, then I could do this to name data  `24 24 23 25` and the game would be none the wiser. 

 The checksum would not realize the difference as I added 1 to one byte and subtracted 1 from another byte keeping the net sum change to nothing. After doing that change and crossing my fingers, it worked! I was met by the game thinking my name is `AA B`! So that is what I did for all 255 (`00 - FF`) possible bytes. Now I have a character encoding table to understand better how the game works! You can view the table [here](https://github.com/jbperr/DWM-SRAM-Data-Dive/blob/main/char_encoding.md).

By figuring out the character encoding, one of my childhood questions had been answered. The default name for the main character in DWM is `TERRY`, but if you want a different name you are limited to only 4 total characters. The encoding table shows why this is a thing. The letters in  `TERRY` are smooshed into 4 tiles so that they can be displayed in 4 bytes. 

Now that the encoding table is done, I can import a text encoding file into my hex editor, I am using Hex Fiend for macOS, so the editor can display what the game would think the bytes mean. On the side of the editor, I can see what the same 9 bytes from above would look like.   

`00 00 00 00 24 24 24 24 F0`

`0  0  0  0  A  A  A  A  . `

Now we can really dig into this save file! But wouldn't it be easier to understand how the save is structured if we could arbitrarily change any byte? Yes!

A json of the character encoding can be found [here](https://github.com/jbperr/DragonWarriorMonstersRE/blob/main/Encoding_Tables/characters.json).

It was nice that we could change a byte by changing another byte in the opposite way, however, there are a few limitations on that method. If we instead reversed the checksum, we could do anything to the save file and then generate a checksum that would trick the game into thinking the save is legit. So let's do it!

# Checksum

If you remember, the checksum is just a simple sum across the whole file. So that result must be stored somewhere we just have to find out where. The quickest way I thought of doing that is going straight to the source and examining the assembly of the game as it saves. That way I can see what bytes are stored, when and where they get stored, and how they get stored there. Using an amazing Game Boy emulator called [Emulicious](https://emulicious.net/), I can use the Debugger to view the disassembly of the game's code to see what is happening. We can view things such as `ld b, a` and `add hl, hl` and `ld a, [_RAM_C899_]`. Perfect! Now we know exactly what is happening, right? Well, after a few days of reading the [Pan Docs](https://gbdev.io/pandocs/CPU_Instruction_Set.html) and the [RGBDS docs](https://rgbds.gbdev.io/docs/v0.6.0/gbz80.7/), yes!

The instruction set isn't too difficult to understand once you have the syntax down. 

The first command is loading, or copying, the value in register `a` to register `b`. 
The second command is adding the value in `hl` into the value in `hl`. This  multiplies whatever value is in `hl` by two. 
The third command loads `a` with the byte that is stored in RAM at position `C899`. 

See? Not too bad, just some syntax to get used to. So, I set a breakpoint to pause the game anytime the game tries to read or write data to the SRAM (the portion of the game memory that stores the save). This allows me to read what is happening in the assembly as the game reads and writes the save file. After some watching and some time to understand everything, I discovered the function that generates the checksum. Here is what happens to every byte of save data with a quick explanation to the side. This function starts at the third byte (index=2).

`_LABEL_2116_:`

1. `00:2116	ldi a, [hl]` - Load `[hl]` into register `a` and then increment `[hl]`. `[hl]` is used as the byte index of the save file. This will start at the third byte. This gives us a clue that the first two bytes might be the checksum.

2. `00:2117	add e` - Add register `e` to register `a`. 

3. `00:2118	ld e, a` - Load register `a` to register `e`. This just copies the result of the addition step back into register `e`.

4. `00:2119	ld a, $00` - Load register `a` with `00`. This will just empty register `a` for the next addition step.

5. `00:211B	adc d` - Add register `d` into register `a` with the carry flag. Which means if the addition in step 2 resulted in a number greater than 255, there would be a flag marked in the `f` register that signifies a carry bit. This would be added onto `d` in this step. 

6. `00:211C	ld d, a` - Load the result of the last step into `d`.

7. `00:211D	dec bc` - Decrement `bc`. `bc` serves as a counter for how many bytes will be processed. (8192).

8. `00:211E	ld a, b` - Load `b` into `a`.

9. `00:211F	or c` - OR `c` and `a`.

10. `00:2120	jr nz, _LABEL_2116_` - If the last result wasn't zero, repeat the loop again starting back at step 1. If it was zero, which means that all the bytes have been processed, then the program will go onto the next instruction and won't jump back to the beginning of the loop.

It is important to note that registers `d` and `e` do not start at `00`, they start at `46` and `38` respectively. In steps 3 and 6, the result of the addtion gets stored in registers `d` and `e`. So if we pay attention to these registers at the end of this process and then look for those bytes in the save file we can figure out where the checksum is stored. And that just so happens to be the first two bytes of the file. Right before where the checksum math starts. Perfect!

My next step from here was to implement something quick in Python to simulate this whenever I want to. You can find this [here](https://github.com/jbperr/DragonWarriorMonstersRE/blob/main/checksum.py), but here is the main loop.
```
for i in range(2, 8192):
    a = save[i] # 1 - LOAD SRAM TO A

    a += e      # 2 - ADD E TO A. If over 255, F becomes a carry flag

    if len(hex(a)) == 5:
        a -= carry
        f += 1

    e = a       # 3 - LOAD A INTO E
    
    a = 0x00    # 4 - LOAD $00 TO A
    
    a += d      # 5 - ADD D AND CARRY TO A

    if f != 0:
        a += f
        f = 0x00

    if len(hex(a)) == 5:
        a -= carry

    d = a       # 6 - LOAD A INTO D
```

Now that we have total control over how the save validates itself, let's move on and figure out what the rest of the save means.

# Interlude

From here on I will go into less detail and just document what I found without a narrative. Everything found is just using a combination of the character encoding to find names and editing the savefile with the checksum to figure out what data controls what.

## Monsters

The first farm section begins at byte 507 and the second farm section begins at byte 4388. Each monster is 149 bytes long. Therefore, in the first farm, the second monster starts at byte 656, the third monster starts at byte 805, etc. There are still some things to figure out, the biggest being the 30 unknown bytes from +101 to +130, but that will eventually be found. My findings can be summarized by this table.

 A json with the monster IDs can be found [here](https://github.com/jbperr/DragonWarriorMonstersRE/blob/main/Encoding_Tables/monsters.json).

 A json with the family IDs can be found [here](https://github.com/jbperr/DragonWarriorMonstersRE/blob/main/Encoding_Tables/family.json).
 
 A json with the skill IDs can be found [here](https://github.com/jbperr/DragonWarriorMonstersRE/blob/main/Encoding_Tables/skills.json).

|  <br>+0 : 507 : 1 byte  	|  <br>Bred/Farm/Party (00/01/02)  	|
|---	|---	|
|  <br>+1 to + 4 : 508-511 : 4 bytes  	|  <br>Monster name  	|
|  <br>+5 to +8 : 512-515 : 4 bytes  	|  <br>F0 F0 F0 F0 spacer  	|
|  <br>+9 : 516 : 1 byte  	|  <br>MONSTER ID  	|
|  <br>+10 : 517 : 1 byte  	|  <br>Family (00-09)  	|
|  <br>+11 : 518 : 1 byte  	|  <br>Sex (00-Male 01-Female) 	|
|  <br>+12 to +15 : 519 - 522 : 4 bytes  	|  <br>OG Masters name  	|
|  <br>+16 to +19 : 523 - 526 : 4 bytes  	|  <br>F0 F0 F0 F0 spacer  	|
|  <br>+20 : 527 : 1 byte  	|  <br>Unknown  	|
|  <br>+21 to +22 : 528 - 529 : 2 bytes  	|  <br>Concatenated Parents ID  	|
|  <br>+23 to +26 : 530 - 533 : 4 bytes  	|  <br>Dad’s Master  	|
|  <br>+27 to +30 : 534 - 537 : 4 bytes  	|  <br>F0 F0 F0 F0 spacer  	|
|  <br>+31 : 538 : 1 byte  	|  <br>Unknown  	|
|  <br>+32 to +35 : 539 - 542 : 4 bytes  	|  <br>Mom’s Master  	|
|  <br>+36 to +39 : 543 - 546 : 4 bytes  	|  <br>F0 F0 F0 F0 spacer  	|
|  <br>+40 : 547 : 1 byte  	|  <br>Unknown  	|
|  <br>+41 to +73 : 548 - 580 : 33 bytes  	|  <br>Skills monster has learned/can learn. The first 8 bytes are currently learned skills. Everything past that is skills that can be learned. 	|
|  <br>+74 : 581 : 1 byte  	|  <br>Unknown  	|
|  <br>+75 : 582 : 1 byte  	|  <br>Current level  	|
|  <br>+76 : 583 : 1 byte  	|  <br>Max level  	|
|  <br>+77 to +79 : 584 - 586 : 3 bytes  	|  <br>Total Exp  	|
|  <br>+80 to +97 : 587 - 604 : 18 bytes  	|  <br>Stats (Current HP, Total HP, Current MP, Total MP, ATK, DEF, AGL, INT, WLD) Each gets 2 bytes incase it goes over 255. If over 255 it is little endian. 271 (0x010f) would be stored as 0x0F 0x01  	|
|  <br>+98 : 605 : 1 byte  	|  <br>Breeding plus  	|
|  <br>+99 : 606 : 1 byte  	|  <br>00 is hatched. 01 is unhatched/egg form  	|
|  <br>+100 : 607 : 1 byte  	|  <br>Personality value  	|
|  <br>+101 to +130 : 608-637 : 30 bytes  	|  <br>Unknown  	|
|  <br>+131 to +134 : 638-641 : 4 bytes  	|  <br>Dad’s Name  	|
|  <br>+135 to +138 : 642-645 : 4 bytes  	|  <br>F0 F0 F0 F0 spacer  	|
|  <br>+139 : 646 : 1 byte  	|  <br>Dad’s breeding plus  	|
|  <br>+140 to +143 : 647-650 : 4 bytes  	|  <br>Mom’s Name  	|
|  <br>+144 to +147 : 651-654 : 4 bytes  	|  <br>F0 F0 F0 F0 spacer  	|
|  <br>+148 : 655: 1 byte  	|  <br>Mom’s breeding plus  	|


### Library
COMING SOON
## Inventory

The inventory takes up 20 bytes total between bytes 395-414. 

A json with the item IDs can be found [here](https://github.com/jbperr/DragonWarriorMonstersRE/blob/main/Encoding_Tables/items.json).

## Bank/Vault
COMING SOON
## Settings
COMING SOON
## Conclusion and Future To-D0
COMING SOON

Last Updated: 11/17/2022