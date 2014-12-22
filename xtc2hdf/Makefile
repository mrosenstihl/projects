CFLAGS = -g -Wall -O3 -std=c99
INCLUDES = -I/opt/local/include/gromacs -I/opt/local/include -I./c-blosc/blosc
LDFLAGS = -L/opt/local/lib -L./c-blosc/blosc
CC = gcc
LIBS =  -lm -lgmx -lhdf5

all: xtc2hdf xtc_index xtc_analyse

xtc2hdf: xtc2hdf.c
	$(CC) $(CFLAGS) $(INCLUDES) $(LDFLAGS) $(LIBS) -o xtc2hdf xtc2hdf.c 
xtc_index: xtc_index.c
	$(CC) $(CFLAGS) $(INCLUDES) $(LDFLAGS) $(LIBS) -o xtc_index xtc_index.c 
xtc_analyse: xtc_analyse.c
	$(CC) $(CFLAGS) $(INCLUDES) $(LDFLAGS) $(LIBS) -lblosc -o xtc_analyse xtc_analyse.c 
clean:
	rm xtc2hdf xtc_index xtc_analyse
