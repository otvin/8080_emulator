# 8080 emulator

Goal is to build a working 8080 Emulator in Python.  

## 8080 Resources:

[Intel 8080 Microcomputer Systems User's Manual - September 1975](http://bitsavers.trailing-edge.com/components/intel/MCS80/98-153B_Intel_8080_Microcomputer_Systems_Users_Manual_197509.pdf)

[8080/8085 Assembly Language Programming Manual](http://bitsavers.org/components/intel/MCS80/9800301D_8080_8085_Assembly_Language_Programming_Manual_May81.pdf).  Starting on page 1-10, there is a discussion of the various flags and how they are set/reset.

## Projects

### Space Invaders
First project with this emulator is to play the original arcade game Space Invaders.  Here are some Space Invaders-specific resources:

[Emulator 101](http://emulator101.com/)

[Annotated disassembly of Space Invaders ROM](https://www.computerarcheology.com/Arcade/SpaceInvaders/Code.html)

[Space Invaders emulator in Javascript](https://bluishcoder.co.nz/js8080/) - easy to run a certain number of instructions and validate register states.  Cannot easily inspect memory (I am sure it can be done with JS debugging tools.)


#### To play

To play Space Invaders, you need to install pygame.  With Python 3.10 or earlier, ```pip install pygame``` works fine.  However, as of this writing there is no wheel for pygame with Python 3.11 or later (see: https://github.com/pygame/pygame/issues/3307).  So you can install with ```pip install pygame --pre```.  You will also need a copy of the four Space Invaders ROMs (invaders.e, invaders.f, invaders.g, and invaders.h) which are not included in this repo due to copyright.  They are easily found on the internet.  Place them in the root folder.  

Space Invaders controls:

* 0 = Deposit Coin
* 1, 2 = 1 and 2 player start
* left/right arrows = move 
* space = fire

Execute the game with ```python space_invaders.py``` (Windows) or ```python3 space_invaders.py``` (Linux)

### CPU Test Suite

Space Invaders does not use all aspects of the CPU.  Before moving to other projects, I want to validate the CPU more thoroughly.  I found a [set of 8080/8085 CPU tests](https://altairclone.com/downloads/cpu_tests/).  I have implemented the first, ```TST8080.COM```, which you can download from that site and place in the root folder.

#### To run

```python3 test8080_system.py```  The test halts the CPU after completing.  CPU can respond to interrupts after an HLT, so the program doesn't end.  You will need to ```CTRL-C``` once you see the completion message.

## Notes

There is a debugger and disassembler included.  To use the debugger, press ESC while executing the game, or start with the debug flag, e.g. ```python3 space_invaders.py -debug```.  The ```?``` command lists all the debugger commands.  Note it looks backwards
10 bytes for the disassembly, which may mean that it improperly interprets multi-byte instructions that preceed the current program counter.  The system will jump to the debugger if there is any python exception while trying to execute a CPU instruction.
