# 8080 emulator

Goal is to build a working 8080 Emulator in Python.  

## 8080 Resources:

[Intel 8080 Microcomputer Systems User's Manual - September 1975](http://bitsavers.trailing-edge.com/components/intel/MCS80/98-153B_Intel_8080_Microcomputer_Systems_Users_Manual_197509.pdf)

[8080/8085 Assembly Language Programming Manual](http://bitsavers.org/components/intel/MCS80/9800301D_8080_8085_Assembly_Language_Programming_Manual_May81.pdf).  Starting on page 1-10, there is a discussion of the various flags and how they are set/reset.

## Projects

First project with this emulator is to play the game Space Invaders.  Here are some Space Invaders-specific resources

[Emulator 101](http://emulator101.com/)

[Annotated disassembly of Space Invaders ROM](https://www.computerarcheology.com/Arcade/SpaceInvaders/Code.html)

[Space Invaders emulator in Javascript](https://bluishcoder.co.nz/js8080/) - easy to run a certain number of instructions and validate register states.  Cannot easily inspect memory (I am sure it can be done with JS debugging tools.)


## To use

To play Space Invaders, you need to install pygame with Python 3.10 or earlier, ```pip install pygame``` works fine.  However, as of this writing there is no wheel for pygame with Python 11 or later (see: https://github.com/pygame/pygame/issues/3307).  So you can install with ```pip install pygame --pre```.  You will also need a copy of the four Space Invaders ROMs (invaders.e, invaders.f, invaders.g, and invaders.h) which are not included in this repo due to copyright.  They are easily found on the internet.  Space Invaders controls:

* 0 = Deposit Coin
* 1, 2 = 1 and 2 player start
* left/right arrows = move 
* space = fire

Execute the game with ```python space_invaders.py``` (Windows) or ```python3 space_invaders.py``` (Linux)

## Notes

There is a debugger and disassembler included.  To use the debugger, press ESC while executing the game, or start with ```python space_invaders.py -debug```.  The ```?``` command lists all the debugger commands.  Note it looks backwards
10 bytes for the disassembly, which may mean that it improperly interprets multi-byte instructions that preceed the current program counter.  