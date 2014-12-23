/*
 Example for reading XTC file.
 Heavily borrowed from "gmxdump.c"
 
 Compile with (one line, adapt the -I and -L paths according to your setup):
 
 gcc -O2 -Wall read_xtc.c -I/usr/local/gromacs/include/gromacs -L/usr/local/gromacs/lib -lgmx xtc_to_hdf.c
 
 
  
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h> 
#include <stdint.h> 

#include "math.h"
#include "gromacs/xtcio.h"

int main(int argc, char *argv[]){	
	/* 
	  argc is the number of arguments, argv is the list of the arguments
	  argv[0] is the excecutable name
	*/
	
	// test if all arguments are given, exit and return to command line if not
	if (argc != 3) {
		printf("Usage: command xtcfile indexfile\n");
		exit(0);
		}
	
	// -------------------- stuff for opening xtc file
	t_fileio* xtc;	
	int natoms,step;
	real time,prec; // current time, precision
	gmx_bool bOK;		// frame OK
	matrix box;		// box size matrix
	rvec *x;		// coordinates array (pointer)
	
	// ------------------- stuff fro HDF5
	
	// -------------------- stuff from command line
	
	char *xtcfile, *indexfile;

	/* 
	  First command line parameter is xtcfile to open.
	  BTW argv[0] is our excecutable filname
	*/
	
	xtcfile =  argv[1];
	printf("Opening %s\n",xtcfile);

	indexfile =  argv[2];
	printf("Opening %s\n",indexfile);

	int nframe = 0;
	
	// open XTC file
	xtc = open_xtc(xtcfile,"r");
	
	// create HDF5 file	
	FILE* index = fopen(indexfile, "w");

	/* Open xtc file, read xtc file first time, allocate memory for x */
	uint64_t pos_now = (uint64_t) gmx_fio_ftell(xtc);
	read_first_xtc(xtc, &natoms, &step, &time, box, &x, &prec, &bOK);
	
	do {
		fprintf(index, "%i 0x%llx\n", nframe, pos_now);
		pos_now = (uint64_t) gmx_fio_ftell(xtc);
		// -------------------- do your stuff here!

		if (nframe%1000 == 0)
			printf("Frame: %6i\n",nframe);

		nframe++;
	}
	// xdr_xtc_seek_frame ist vielleicht schneller, leider kein richtiges API
	while (read_next_xtc(xtc, natoms, &step, &time, box, x, &prec, &bOK));
	
	
	fclose(index);
	close_xtc(xtc);
	return 0;
}
