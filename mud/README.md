All source code necessary to recompile the executables for converting binary files to histogram files.As far as I can tell you need to actually recompile the program on a Mac, Linux and Windows machine to get executables that work with each.

Windows: i686-w64-mingw32-gcc -o FACILITY_SYSTEM.exe *.c -lm -lssp

Linux: gcc *.c -lm -o FACILITY_SYSTEM

Mac: gcc *.c -lm -o FACILITY_SYSTEM
