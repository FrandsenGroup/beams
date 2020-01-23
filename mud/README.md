All source code necessary to recompile the MUD.exe executable. If any changes need to be made, I suggest going into the BEAMS_MUD.c file, make the edits, then recompile with the following commands. As far as I can tell you need to actually recompile the program on a Mac, Linux and Windows machine to get executables that work with each.

Windows: i686-w64-mingw32-gcc -o MUD.exe *.c -lm -lssp

Linux: gcc *.c -lm -o MUDC

Mac: gcc *.c -lm -o MUDM
