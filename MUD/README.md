All source code necessary to recompile the MUD.exe executable. If any changes need to be made, I suggest going into the BEAMS_MUD.c file, make the edits, then recompile with the following commands.

i686-w64-mingw32-gcc -o MUD.exe *.c -lm -lssp
gcc *.c -lm -o MUDC
