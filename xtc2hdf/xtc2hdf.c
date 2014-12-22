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
#include "hdf5.h"
#include "hdf5_hl.h"
#include "math.h"
#define NBIT 0
#define ZIP 7
#define SCALEOFF 1
#define SHUFFLE 1

#define DIMS 3


typedef struct {
   double bx[3];
} the_box_attribute;


int main(int argc, char *argv[]){	
	/* 
	  argc is the number of arguments, argv is the list of the arguments
	  argv[0] is the excecutable name
	*/
	
	// test if all arguments are given, exit and return to command line if not
	if (argc != 3) {
		printf("Usage: command xtcfile h5file\n");
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
	
	int hdf5;
	int status;
	hid_t    dataset, datatype, dataspace;
	char data_set_name[50];


	// -------------------- stuff from command line
	
	char *xtcfile, *h5file;

	/* 
	  First command line parameter is xtcfile to open.
	  BTW argv[0] is our excecutable filname
	*/
	
	xtcfile =  argv[1];
	printf("Opening %s\n",xtcfile);

	h5file =  argv[2];
	printf("Opening %s\n",h5file);


	
	/*
	  Example allocate memmory from heap, dynamically, i.e. not known 
	  at compile time. 
	
	  if it is not needed anymore free the memory with free(variable);
	  See K&R pp.160
	*/
	

	// -------------------- generic variables
	int nframe = 0;
	int i,j;
	int min=0, max=0, total_max=0, total_min=0, val, min_bits;
	
	// ----------------------- attributes
	hsize_t one[1]={1};
	
	// open XTC file
	xtc = open_xtc(xtcfile,"r");
	
	// create HDF5 file	
	hdf5 = H5Fcreate (h5file, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);

	/* Open xtc file, read xtc file first time, allocate memory for x */
	read_first_xtc(xtc, &natoms, &step, &time, box, &x, &prec, &bOK);
	
	// its a flat array, 2D is not so easy ...
	
	void *coordinates;
	coordinates = (int *) calloc(natoms*DIMS, sizeof(int));
	int16_t *coordinates_int16;
	coordinates_int16 = (int16_t *) calloc(natoms*DIMS, sizeof(int16_t));
	int32_t *coordinates_int32;
	coordinates_int32 = (int32_t *) calloc(natoms*DIMS, sizeof(int32_t));

	printf("32bit - Allocated %.1f kB/frame\n", (double) natoms*DIMS*sizeof(int32_t)/1024);
	printf("16bit - Allocated %.1f kB/frame\n", (double) natoms*DIMS*sizeof(int16_t)/1024);



	do {
		printf("Tell filepos: %8i %8x\n", nframe, (long int) gmx_fio_ftell( xtc));
		// -------------------- do your stuff here!

		if (nframe%1000 == 0)
			printf("Frame: %6i\n",nframe);
		// convert coordinates to integer values (values are fixed precision)
		// and record min/max for every frame
		min = 0;
		max = 0;
		for (i=0; i < natoms; i++) {
			for (j=0; j < DIMS; j++) {
				
				val = (int)(x[i][j]*prec);
				
				
				coordinates_int32[i*DIMS+j] = val;
				if (max < val) max = val;
				if (min > val) min = val;
				
			};

		};

		// hid_t xferplist = H5Pcreate(H5P_DATASET_XFER);
		
		if (total_max < max) total_max = max;
		if (total_min > min) total_min = min;
		
		min_bits = (int)(ceil(log2(max-min+1))) + 1;  // minimum bits needed for saving data set + sign bit!
		if (min_bits <= 16) {
			for (i=0; i < natoms; i++) {
				for (j=0; j < DIMS; j++) {
					coordinates_int16[i*DIMS+j] = (int16_t)coordinates_int32[i*DIMS+j];
				};
			};
			coordinates = (int16_t*) coordinates_int16;
			//printf("using 16bit\n");
		}
		else {
			coordinates = (int32_t*) coordinates_int32;
			printf("using 32bit\n");
		};
				
		if (nframe%1000 == 0) 
			printf("\tmin=%i, max=%i, nbits=%i\n", min, max, min_bits);

		// dimension of array in hdf5 file
		hsize_t dimsf[2];

		// chunk dimension for hdf5 file
		
		hsize_t	chunk_dims[2];
		// boxsize
		hsize_t boxsize_dims[1];
		
		dimsf[0] = natoms; // all atoms
		dimsf[1] = DIMS;  // x,y,z coordinates


		// set the HDF chunk size
		chunk_dims[0] = natoms;
		chunk_dims[1] = DIMS;

		if (nframe == 0)
			printf("Chunk size: %i, %i\n", (int) chunk_dims[0], (int)chunk_dims[1]);

		boxsize_dims[0] = 3;
//		boxsize_dims[1] = 3;
		
		/*
		Create dataspace h5screate_simple(rank, dims, maxdims) 
		*/
		
		dataspace = H5Screate_simple(2, dimsf, NULL);

		/*
		Define datatype for the data in the file.
		
		ANSI C9x-specific native integer datatypes
		Signed integer (2's complement), unsigned integer, and bitfield
		8-bit, 16-bit, 32-bit, and 64-bit
		LEAST -- storage to use least amount of space 
		FAST -- storage to maximize performance

		H5T_NATIVE_INT8
		H5T_NATIVE_UINT8
		H5T_NATIVE_INT_LEAST8
		H5T_NATIVE_UINT_LEAST8
		H5T_NATIVE_INT_FAST8 
		H5T_NATIVE_UINT_FAST8
		
		H5T_NATIVE_INT16
		H5T_NATIVE_UINT16
		H5T_NATIVE_INT_LEAST16
		H5T_NATIVE_UINT_LEAST16
		H5T_NATIVE_INT_FAST16
		H5T_NATIVE_UINT_FAST16
		
		H5T_NATIVE_INT32
		H5T_NATIVE_UINT32
		H5T_NATIVE_INT_LEAST32
		H5T_NATIVE_UINT_LEAST32
		H5T_NATIVE_INT_FAST32
		H5T_NATIVE_UINT_FAST32
		
		H5T_NATIVE_INT64
		H5T_NATIVE_UINT64
		H5T_NATIVE_INT_LEAST64
		H5T_NATIVE_UINT_LEAST64 
		H5T_NATIVE_INT_FAST64
		H5T_NATIVE_UINT_FAST64

		*/

		datatype     = H5Tcopy( (min_bits <= 16) ? H5T_NATIVE_INT_LEAST16 : H5T_NATIVE_INT_LEAST32); // data type on disk

		status = H5Tset_order(datatype, H5T_ORDER_LE); // Little-Endian
		if (status != 0) 
			printf("ERROR");
		


		// Create dataset creation property list
		hid_t plist;
		plist = H5Pcreate(H5P_DATASET_CREATE);
		H5Pset_chunk(plist, 2, chunk_dims);  // chunk size
		

		// scale offset filter
		if ( SCALEOFF == 1 ) {
			if (nframe == 0)
				printf("using scale-offset compression\n");
			// status = H5Pset_scaleoffset( plist , H5Z_SO_INT, min_bits); // scale offset
			status = H5Pset_scaleoffset( plist , H5Z_SO_INT, H5Z_SO_INT_MINBITS_DEFAULT); // scale offset
		}

		// n-bit filter
		if ( NBIT==1 ) {
			int offset = 0;
			if (nframe == 0)
				printf("using n-bit compression: %i minimum bits, %i offset\n", min_bits, offset);
			
			// set datatype precision
			if( H5Tset_precision(datatype, min_bits)<0 ) {
				printf("Error: fail to set precision\n");
				return -1;
			}

			// set offset
			if( H5Tset_offset(datatype, offset)<0 ) {
				printf("Error: fail to set offset\n");
				return -1;
			}

			// activate n-bit filter
			status = H5Pset_nbit( plist );
		}
		//
		// shuffle data
		if ( SHUFFLE == 1 ){
			if (nframe == 0)
				printf("using shuffle\n");
			H5Pset_shuffle( plist ); // enable shuffle algorithm
		}


		// compression
		if ( ZIP > 0 ){
			/* disabled for performance */
			if (nframe == 0)
				printf("using gzip compression, level %i\n",ZIP);
			H5Pset_deflate( plist, ZIP); // gzip compression level
		}
		/* link property list */
		hid_t link_plist;
		link_plist = H5Pcreate(H5P_LINK_CREATE);

		/* create intermediate group if missing */
		H5Pset_create_intermediate_group( link_plist, 1 ); 

		/*
		Create a new dataset within the file using defined 
		dataspace and datatype. No properties are set.
		*/
		
		sprintf(data_set_name, "/set_%07i/dset_%03i",nframe/1000*1000,nframe%1000);
		//printf("%s\n",data_set_name);

		if ( (dataset = H5Dcreate(hdf5, data_set_name, datatype, dataspace, link_plist, plist, 0)) < 0 )
		//if ( (dataset = H5Dcreate(hdf5, data_set_name, datatype, dataspace, plist)) < 0 )
			printf("Error: create dataset failed");
		
		// write data set, datatype given here must match the type in memory!
		status = H5Dwrite(dataset, datatype, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates);
		if (status != 0)
			printf("Error writing dataset %i",nframe);
		H5Sclose(dataspace); // or leaks will occur! (http://www.hdfgroup.org/HDF5/doc/RM/RM_H5S.html)
		
		H5Tclose(datatype);		
		
		
		
		/*
		Attributes:
		*/
		double boxs[DIMS];
		for (i=0; i<DIMS; i++){
			boxs[i] = box[i][i];
			};


		hid_t attribute_box, attribute_time, attribute_step, attribute_prec;
		hid_t dataspace_boxsize, dataspace_time, dataspace_step, dataspace_prec;
		
		
		dataspace_boxsize = H5Screate_simple(1, boxsize_dims, NULL);

		
		dataspace_boxsize = H5Screate_simple(1, boxsize_dims, NULL);
		dataspace_time = H5Screate_simple(0, one, NULL);
		dataspace_step = H5Screate_simple(0, one, NULL);
		dataspace_prec = H5Screate_simple(0, one, NULL);


		
		attribute_box = H5Acreate( dataset, "box", H5T_NATIVE_DOUBLE, dataspace_boxsize, H5P_DEFAULT, H5P_DEFAULT );
		H5Awrite(attribute_box, H5T_NATIVE_DOUBLE, boxs);
		H5Aclose(attribute_box);

		double time_d = time;
		attribute_time = H5Acreate( dataset, "time", H5T_NATIVE_DOUBLE, dataspace_time, H5P_DEFAULT, H5P_DEFAULT );
		H5Awrite(attribute_time, H5T_NATIVE_DOUBLE, &time_d);
		H5Aclose(attribute_time);
		
		attribute_step = H5Acreate( dataset, "step", H5T_NATIVE_INT, dataspace_step, H5P_DEFAULT, H5P_DEFAULT );
		H5Awrite(attribute_step, H5T_NATIVE_INT, &step);
		H5Aclose(attribute_step);

		int prec_i = prec;
		attribute_prec = H5Acreate( dataset, "precision", H5T_NATIVE_INT, dataspace_prec, H5P_DEFAULT, H5P_DEFAULT );
		H5Awrite(attribute_prec, H5T_NATIVE_INT, &prec_i);
		H5Aclose(attribute_prec);

		
		
		H5Dclose(dataset); // close dataset, dataspace and datatype 
				

		if ( (nframe % 1000) == 0 ) {
			H5Fflush(hdf5, H5F_SCOPE_GLOBAL);
	//		printf("Flushing at frame %i\n",nframe);
			}
		
		// -------------------- end do you stuff 
		
		// increase frame counter, needed for while statement

		nframe++;
	//	if (nframe == 5000) break;
	}
	// read until file is finnished or  nframe <  $some_number ... 
	while (read_next_xtc(xtc, natoms, &step, &time, box, x, &prec, &bOK));
	
	free(coordinates); // coordinates written not needed anymore		
	
	// write the total number of frames to the first data_set
	hid_t dataspace_totalframes, attribute_totalframes;
	sprintf(data_set_name, "/set_%07i/dset_%03i",0,0);
	dataset = H5Dopen(hdf5, data_set_name, H5P_DEFAULT);
	dataspace_totalframes = H5Screate_simple(0, one, NULL);
	attribute_totalframes = H5Acreate( dataset, "total_frames", H5T_NATIVE_INT, dataspace_totalframes, H5P_DEFAULT, H5P_DEFAULT );
	H5Awrite(attribute_totalframes, H5T_NATIVE_INT, &nframe);
	H5Aclose(attribute_totalframes);
	H5Dclose(dataset);
	H5Fflush(hdf5, H5F_SCOPE_GLOBAL);

	status = H5Fclose (hdf5);
	printf("\n\n\nLast Frame: %i\nAtoms: %i\n",nframe,natoms);
	printf("Max: %i\nMin: %i\n", total_max, total_min);
	//close XTC file
	printf("Quitting ..........\n");
	close_xtc(xtc);
	return 0;
}
