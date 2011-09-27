CFLAGS = -g -Wall -O3 -C99 -strict
INCLUDES = -I/usr/local/gromacs/include/gromacs -I/opt/local/include
LDFLAGS = -L/usr/local/gromacs/lib -L/opt/local/lib
CC = gcc
LIBS =  -lm -lgmx -lhdf5

all: xtc_to_hdf analyse

xtc2hdf:
	$(CC) $(CFLAGS) $(INCLUDES) $(LDFLAGS) $(LIBS) -o xtc2hdf xtc2hdf.c 
clean:
	rm xtc2hdf 
