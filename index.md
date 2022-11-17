# [Save Viewer/Editor](https://www.benperry.org/dwm)
# Dragon Warrior Monsters Save Reverse Engineer

Dragon Warrior Monsters (DWM) is one of my favorite childhood video games. I would always find myself playing it over and over again. It is similar to Pokemon in its monster collecting and monster fighting game-loop. DWM allows you to tame monsters, that live behind portals called gates, and battle those monsters in a tournament with the eventual goal of saving your sister. 

This past couple years I have gotten interested in reverse engineering and trying to understand how things work. After seeing what [PKHeX](https://github.com/kwsch/PKHeX) can do with Pokemon saves, I wanted to see what I could make for DWM. The save file structure has been extensively studied and documented for every Pokemon game; whereas, for DWM there really is not much. I would have to go from the ground up. I decided to start by looking at the save file structure for [Generation 2 Pokemon](https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_%28Generation_II%29) as it would most likely be the most similar as the games were made around the same time (1998 for DWM and 1999 for Pokemon Gold/Silver). I knew that the save structures wouldn't be the exact same, but it allowed me to spot some patterns such as using a [similar structure](https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_%28Generation_II%29#Pok.C3.A9dex_owned.2C_Pok.C3.A9dex_seen) to store whether a certain Pokemon or certain monster or how the checksum is used to validate the save. To start, I just opened up the save in a hex editor to see what was going on. But hold on, what even is a Game Boy save?


## Game Boy Saves

All Game Boy games that had a save file (Pokemon Gold, Zelda: Link's Awakening, DWM) had a battery in the cartridge that kept some of the cartridge's memory on all the time so that data could be kept. This is why a lot of people recently have been turning on their old Pokemon game and finding that the save has disappeared. The battery died and with it the data too. Luckily, you can replace the batteries and you can extend the life of the data; however, in order to replace the battery, the saves will get lost as the power will be cut while the battery is disconnected. There is another way to protect your saves though. A [Sanni Cart Reader](https://github.com/sanni/cartreader) can be used to read and write saves, read game roms, and much more from GB/C/A, NES, SNES, N64, SEGA consoles, etc. In 2021, I built a modification of the Sanni reader by [makho](https://github.com/makhowastaken/cartreader) to preserve all my old Game Boy game saves. Anyways, with that basic information out of the way. I dumped my save and then opened it in a hex editor to see what was going on.

## DWM Character Encoding

`FC 77 01 00 02 00 00 03 01 00 40 18 01 80 B8 00 11 0B 18 01 B8 00 E0 01 00 01 00 00 00 00 78 00 38 00 0F 4F 01 02 00 00 00 03 C0 06 D5 CE E5 D5 00 3B 01 00 00 09 00 E8 00 48 00 02 03 11 00 00 05 80 07 14 9A 1C A7 03 07 00 00 14 9A 00 02 00 00 FF FF B4 9B 00 00 02 04 FF 00 00 00 00 00 05 FF D8 00 B8 00 00 00 00 00 00 8E CA 01 02 01 15 0C 0A 0A 04 1D 45 03 0F 00 00 F9 C5 C9 F6 67 0A ...`

Here are the first 128 of 8192 bytes of the the save file. At first, it is a lot to look at. But after reading the page on [Pokemon character encoding](https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_II)), I figured the first step is to figure out how the text gets stored. I did this by starting up a new save and naming myself `AAAA` so that I can then look in the save file for four bytes that repeat themself. After examining that save file, I found where your name gets stored. Here are bytes 374-384.   

 `00 00 00 00 24 24 24 24 F0` 

 You can see the byte `24` repeated four times from byte 380 to byte 383. So now we know that 'A' is represented by `24`, but what about everything else? Well we could start up a new save file and name ourselves a mix of characters and then record what gets saved as our name. However, that would take a long time compared to if we could just edit the hex and then load the save to view how the name changed. So I tried just that and changed the name bytes to `25 25 25 25`. I loaded up the save to see what happened and was greeted by the game showing me there was no save game to be loaded. This is what happens when the save is corrupted or there is no save to be loaded. This tells me the game uses some kind of checksum to determine validity of a save file. From reading how Pokemon implements a checksum, I hoped it would be some sort of simple sum across the whole file and then that data would be stored somewhere in the file. If it was just a sum, then I could do this to name data  `24 24 23 25` and the game would be none the wiser. 

 The checksum would not realize the difference as I added 1 to one byte and subtracted 1 from another byte keeping the net sum change to nothing. After doing that change and crossing my fingers, it worked! I was met by the game thinking my name is `AA B`! So that is what I did for all 255 (`00 - FF`) possible bytes. Now I have a character encoding table to understand better how the game works! You can view the table [here](https://github.com/jbperr/DWM-SRAM-Data-Dive/blob/main/char_encoding.md).

By figuring out the character encoding, one of my childhood questions had been answered. The default name for the main character in DWM is `TERRY`, but if you want a different name you are limited to only 4 total characters. The encoding table shows why this is a thing. The letters in  `TERRY` are smooshed into 4 tiles so that they can be displayed in 4 bytes. 

Now that the encoding table is done, I can import a text encoding file into my hex editor, I am using Hex Fiend for macOS, so the editor can display what the game would think the bytes mean. On the side of the editor, I can see what the same 9 bytes from above would look like.   

`00 00 00 00 24 24 24 24 F0`

`0  0  0  0  A  A  A  A  . `

Now we can really dig into this save file! But wouldn't it be easier to understand how the save is structured if we could arbitrarily change any byte? Yes!

It was nice that we could change a byte by changing another byte in the opposite way, however, there are a few limitations on that method. If we instead reversed the checksum, we could do anything to the save file and then generate a checksum that would trick the game into thinking the save is legit. So let's do it!
## Checksum

If you remember, the checksum is just a simple sum across the whole file. So that result must be stored somewhere we just have to find out where. The quickest way I thought of doing that is going straight to the source and examining the assembly of the game as it saves. That way I can see what bytes are stored, when and where they get stored, and how they get stored there. Using an amazing Game Boy emulator called [Emulicious](https://emulicious.net/), I can use the Debugger to view the disassembly of the game's code to see what is happening. We can view things such as `ld b, a` and `add hl, hl` and `ld a, [_RAM_C899_]`. Perfect! Now we know exactly what is happening, right? Well, after a few days of reading the [Pan Docs](https://gbdev.io/pandocs/CPU_Instruction_Set.html) and the [RGBDS docs](https://rgbds.gbdev.io/docs/v0.6.0/gbz80.7/), yes!

The instruction set isn't too difficult to understand once you have the syntax down. 

The first command is loading, or copying, the value in register `a` to register `b`. 
The second command is adding the value in `hl` into the value in `hl`. This  multiplies whatever value is in `hl` by two. 
The third command loads `a` with the byte that is stored in RAM at position `C899`. 

See? Not too bad, just some syntax to get used to. Then, I set a breakpoint so anytime the game tries to read or write any data to the SRAM (the portion where the save is stored) the emulator pauses and I can see what the game is doing in the assembly.

## Monsters
COMING SOON
### Library
COMING SOON
## Inventory
COMING SOON
### Bank/Vault
COMING SOON
## Settings
COMING SOON
## Conclusion and Future To-D0
COMING SOON