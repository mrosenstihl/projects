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

/*
 * int8_t
 * int16_t
 * int32_t
 * uint8_t
 * uint16_t
 * uint32_t[Option End]
 *
 */

#include "xtcio.h"
#include "math.h"

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
	
	char *xtcfile, *indexfile_name;

	/* 
	  First command line parameter is xtcfile to open.
	  BTW argv[0] is our excecutable filname
	*/
	
	xtcfile =  argv[1];
	printf("Opening %s\n",xtcfile);

	indexfile_name =  argv[2];
	printf("Opening %s\n",indexfile_name);

	// open XTC file
	xtc = open_xtc(xtcfile,"r");
	
	// create HDF5 file	
	FILE* fp_index = fopen(indexfile_name, "r");
    
    // read index file
    uint64_t number_of_indexes=128;
    // this will be our frameno=filepos array: fseekpos[frameno] = filepos
    uint64_t* fseekpos = (uint64_t*) calloc(number_of_indexes, sizeof(uint64_t));
    // read data into this variables
    uint64_t a_frame, a_fpos;
    // this holds our maximum frame number
    uint64_t max_frame = 0;
    uint64_t i = 0;
    while(fscanf(fp_index, "%lli %llx\n", &a_frame, &a_fpos)==2){
        // check maxmimum frame number
        if (a_frame > max_frame) max_frame = a_frame;
        // increase array size if necessary
        if (number_of_indexes <= max_frame){
            number_of_indexes += number_of_indexes/2; // increase number_of_indexes
            fseekpos = (uint64_t*) realloc(fseekpos, number_of_indexes*sizeof(uint64_t));
        }
        // store frame position
        fseekpos[a_frame] = a_fpos;
        i++;
        printf("%lli %lli\n", a_frame, a_fpos);
    }
    fclose(fp_index);
    number_of_indexes = i;
    // fix array size
    fseekpos = (uint64_t*) realloc(fseekpos, number_of_indexes*sizeof(uint64_t));

    /* Open xtc file, read xtc file first time, allocate memory for x */
    read_first_xtc(xtc, &natoms, &step, &time, box, &x, &prec, &bOK);

    for (int nframe=0; nframe <= 10000; nframe +=10){
        int frame = rand()%10000;
        //select frame and read it
        gmx_fio_seek(xtc, fseekpos[frame]);
        printf("%i: %f %f %f\n",step,x[3800][0], x[3800][1], x[3800][2]);
        read_next_xtc(xtc, natoms, &step, &time, box, x, &prec, &bOK);
    }
	
	
	close_xtc(xtc);
	return 0;
}
