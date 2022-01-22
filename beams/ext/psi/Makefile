test.exe : main.o MuSR_td_PSI_mdubin.o 
	g++ -o testmdu main.o MuSR_td_PSI_mdubin.o 

main.o : main.cpp MuSR_td_PSI_mdubin.h Makefile
	g++ -c main.cpp
MuSR_td_PSI_mdubin.o : MuSR_td_PSI_mdubin.cpp MuSR_td_PSI_mdubin.h tydefs.h Makefile
	g++ -c MuSR_td_PSI_mdubin.cpp
clean :
	rm testmdu main.o MuSR_td_PSI_bin.o

