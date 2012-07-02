#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <limits.h> // for int limits etc.
#include <assert.h>
#include <time.h>
#include <gsl/gsl_histogram.h>
#include <omp.h>

#include "main.h"
#include "dSFMT-src-2.1/dSFMT.h"
//#include "ziggurat/ziggurat.h"

//#define STATS
#define MULTIPLIER 1000000  // seperates the coordiantes (poor man's hash) 

int main (int argc, char * argv[]) {
	int num_particles = DSFMT_N64*4;
	int num_defects = 1024*4;
	int box_size = 128;
	long long nsteps = 1024*1024*2;
	
	//omp_init_lock(&omplock);
	//omp_set_num_threads(1);
	if (argc == 5) {
		num_particles = atoi(argv[1]);
		num_defects = atoi(argv[2]);
		box_size = atoi(argv[3]);	
		nsteps = atoll(argv[4]);	
	}
	else {
		printf("\n# ***** Using default values! *****\n\n");
		printf("# usage: rw #particles #defects #box #steps\n");
		
	}
	
	// Information:
	printf("#-------------------- Paramters --------------------\n");
	printf("# Particles: %i\n", num_particles);
	printf("# Box size: %i\n", box_size);
	printf("# Defects: %i (Density: %.2e)\n", num_defects, (float) num_defects/pow(box_size,3) );
	printf("# Steps: %lli\n", nsteps);
	printf("#---------------------------------------------------\n");
	
	assert( (box_size & (box_size - 1)) == 0 ); // check if box_size is power of two
	//zigset(1);
	dsfmt_t dsfmt;
	
	int seed = 1;
	
	// int num_random  = (num_particles < 1024) ? 1024: num_particles;
	// int  *correlation_times = malloc(num_particles * sizeof(int)); // random distribution of correlation times
	// char *directions = malloc(nsteps*sizeof(char)); // directions
	int **particles = malloc2D_i(num_particles, 4); // 2d array for particles: x,y,z,mag
	int **defects = malloc2D_i(num_defects, 3); // 2d array for defect coordinates
	
	//int *particle;
	//int direction;
	
	
	// init random number generator
	dsfmt_init_gen_rand(&dsfmt, seed);
	
	// check if we can create the hashes
	//assert(box_size < MULTIPLIER);
	assert(num_defects < pow(box_size,3));
	
#ifdef STATS
	// statistics
	// histogram of diretions
	gsl_histogram * h = gsl_histogram_alloc (6);
	gsl_histogram_set_ranges_uniform (h, 0, 6);
	
	// histogram of visits
	gsl_histogram * hvisits = gsl_histogram_alloc (10000);
	gsl_histogram_set_ranges_uniform (hvisits, 0, 10000);
	
	// gsl histogram seems not to be thread safe, allow only 1 thread
	omp_set_num_threads(1);
#endif
	
	// Start simulation
	
	// distribute particles from 0 to +box_size
	for (int j = 0; j < 3; j++) {
		for (int i=0 ;i < num_particles; i++) {
			particles[i][j] = (int) (dsfmt_genrand_close_open(&dsfmt)*box_size);
		}
	}
	
	
	// distribute defects from 0 to +box_size
	for (int j = 0; j < 3; j++) {
		for (int i=0 ; i < num_defects; i++) {
			int val = (int) (dsfmt_genrand_close_open(&dsfmt)*box_size);
			defects[i][j] = val;
		}
	}
	
	// METHOD 1: now create a hashed list to find them later
	// This will be a fallback to METHOD 2, in case memory is not enough
	int64_t *hash_list = malloc( num_defects*sizeof(int64_t) );
	for (int i = 0; i < num_defects; i++) {
		hash_list[i] = hash(defects[i][0],defects[i][1],defects[i][2]);
	}
	
	qsort(hash_list, num_defects, sizeof(int64_t), int64_cmp);
	
	// METHOD 2: create lookup table for x -> lookup table for y -> lookup table for z 
	// The smart thing is that the pointers are NULL if there is no defect in the corresponding slab,
	// so only the z coordinates are really arrays
	//
	// If I need more space one could use the chars as bit fields,
	// One needs to calculate the offset (or index of char) to get to the proper group though.
	// get offset: offset = coord/sizeof(char) oder coord >> log2(sizeof(char))
	// set bit: array[offset] |= 1 << coord%sizeof(char)
	
	// in check_defekt_3d:
	// check bit: array[offset] & 1 << coord%sizeof(char)  > 1
	//
/*
	int mem_size_table = 0;
	// first coordinate (x) will be an array of pointers to an array of pointers
	char ***lookup_table = malloc(box_size * sizeof(char**));
	mem_size_table += box_size * sizeof(char**);
	// initialize the arrays to NULL pointer
	for (int i = 0; i < box_size; i++) {
		lookup_table[i]=NULL;
	}
	
	for (int i = 0; i < num_defects; i++) {
		int x_index = defects[i][0];
		int y_index = defects[i][1];
		int z_index = defects[i][2] / sizeof(char);
		// check if there  is already an array at x_index ...
		if (lookup_table[x_index] == NULL) {
			// ... it's not! Create an array of pointers for the second coordinate
			lookup_table[x_index] = malloc(box_size * sizeof(char*)); // malloc second coordinate pointers
			mem_size_table += box_size * sizeof(char*);
			for (int i = 0; i < box_size; i++) 
				lookup_table[x_index][i]=NULL; // initialize the second coordiante pointers to NULL
		}
		
		// check if there is already an array at [x_index][y_index]		
		if (lookup_table[x_index][y_index] == NULL) { // check if third coordinate array exists
			lookup_table[x_index][y_index] = malloc(box_size * sizeof(char)); // malloc third coordinate array
			mem_size_table += box_size * sizeof(char);
			for (int i = 0; i < box_size; i++) 
				lookup_table[x_index][y_index][i]=0; // initialize the third array to zero
			
		}
		// set the defect coordinate
		lookup_table[x_index][y_index][z_index] = 1;

		 }

	int test_particle[4];
	double start = omp_get_wtime();
	for (int i = 0; i < 1024*1024*128; i++) {
		for (int j = 0; j < 3; j++) {
			test_particle[j] = (int) (dsfmt_genrand_close_open(&dsfmt)*box_size);
		}
		check_defect_3d(test_particle, lookup_table, 10);
	}
	double stop = omp_get_wtime();
	printf("# Time Method 2: %.2fs\n", stop-start);
	printf("# Lookup table size M1: %10.1fkB %i %i\n",  mem_size_table/((float) (1024)), num_defects, box_size);

*/
	
	// Method 3: Using the scheme above but for x,y,z seperately
	int ltb_N = (int) ceil( ( (double)box_size ) / sizeof(int));
	int xltb[ltb_N];
	int yltb[ltb_N];
	int zltb[ltb_N];
	for (int i = 0; i < ltb_N; i++) {
		xltb[i]=0;
		yltb[i]=0;
		zltb[i]=0;
	}
	for (int i = 0; i < num_defects; i++) {
		int xi =  defects[i][0] / sizeof(int);
		int xbit = defects[i][0] % sizeof(int);
		//printf("x %i %i %i %i\n",i, defects[i][0], xi, xbit);

		xltb[xi] |= 1 << xbit;

		int yi = defects[i][1] / sizeof(int);
		int ybit = defects[i][1] % sizeof(int);
		yltb[yi] |= 1 << ybit;
		//printf("y %i %i %i %i\n",i, defects[i][1], yi, ybit);

		int zi = defects[i][2] / sizeof(int);
		int zbit = defects[i][2] % sizeof(int);
		zltb[zi] |= 1 << zbit;
		//printf("z %i %i %i %i\n",i, defects[i][2], zi, zbit);
	}

/*
	start = omp_get_wtime();
	for (int i = 0; i < 1024*1024*128; i++) {
		for (int j = 0; j < 3; j++) {
			test_particle[j] = (int) (dsfmt_genrand_close_open(&dsfmt)*box_size);
		}
		check_defect_ltb(test_particle, xltb, yltb, zltb , 0);
	}
	stop = omp_get_wtime();
	printf("Time Method 3: %.2fs\n", stop-start);
*/	
	
	printf("# Lookup table size M2: %10.1fkB %i %i\n",  3*ltb_N*sizeof(int) / ((float) (1024)), num_defects, box_size);

	// check if the lookup table is correct
	for (int i = 0; i < num_defects; i++) {

		int x = defects[i][0];
		int y = defects[i][1];
		int z = defects[i][2];
		//printf("Test: %i\n",lookup_table[x][y][z]);
/*
		assert(lookup_table[x][y][z] == 1); // Method 2
*/
		// Method 3
		int xi = x/ sizeof(int);
		int xbit = x % sizeof(int);
		assert( (xltb[xi] & (1<<xbit)) != 0 ); 

		int yi = y/ sizeof(int);
		int ybit = y % sizeof(int);
		assert( (yltb[yi] & (1<<ybit)) != 0 ); 


		int zi = z/ sizeof(int);
		int zbit  = z % sizeof(int);
		assert( (zltb[zi] & (1<<zbit)) != 0 ); 

		
	}

	
	
	/*
	 for (int i = 0; i < num_particles; i++) {
	 if (particles[i][3] == 1) printf("%i\n", i);
	 }
	 */
	
	
	
	/******************************* loop *********************************/
	// exchange outer with inner loop
	printf("\n# Starting ...\n");
	
	int  *mags = malloc(nsteps * sizeof(int)); // magnetization per step
	for (int i = 0; i < nsteps; i++) {
		mags[i] = 0;
	}
	
	
	// loop over particles
	double calc_time=0;
	printf("MinSize: %i\n", DSFMT_N64);
	double *dir_pool = malloc(DSFMT_N64 * sizeof(double));
#pragma omp parallel for reduction(+:calc_time) firstprivate(dir_pool)
	for (int i = 0; i < num_particles; i+=DSFMT_N64) {
		// every thread gets its own RNG
		dsfmt_t dsfmt;
		dsfmt_init_gen_rand(&dsfmt, i);
		
		/*
		 double *random_numbers_steps = malloc(nsteps * sizeof(double));		
		 // create random numbers for the movements (directions 1..6)
		 dsfmt_fill_array_open_close(&dsfmt, random_numbers_steps, nsteps);
		 
		 // scale the to 0,1,2,3,4,5 (the 6 directions)
		 for (int i=0 ;i < nsteps; i++) {
		 directions[i] = (short) (random_numbers_steps[i]*6);
		 }
		 free(random_numbers_steps);
		 */
		
		// distribution of correlation times, rexp,rnor are NOT thread safe!
		//for (int i=0 ;i < num_particles; i++) {
		//	correlation_times[i] = (int) rexp()*30;
		//}
		
		// loop over steps
		for (int step = 0; step < nsteps; step++) {
			dsfmt_fill_array_open_close(&dsfmt, dir_pool, DSFMT_N64);
			double start = omp_get_wtime();
			// doing batches of particles
			for (int j = 0; j < DSFMT_N64; j++) { 
				int* particle = particles[i+j];
				int direction = dir_pool[j];
				//int direction = (int) (dsfmt_genrand_close_open(&dsfmt)*6); 
				// only move particles which have not met defect yet == 0
				// or see how often they met a defefct >= 0
				if (particle[3] == 0) { 
					
					// random step
					move_particle(particle, direction);
					
					// obey periodic boundary conditions, i.e. fold back
					check_pbc(particle, box_size);
					
					int tc = 10;
					
					// check_defect(particle, tc , hash_list, num_defects);
					// check_defect_tlb(particle, tc, hash_min, span, defekt_ltb);
					// check_defect_3d(particle, lookup_table, tc);
					check_defect_ltb(particle, xltb, yltb, zltb , tc);

					// ref_check_defect(particle, defects, num_defects);
				}
				else { // particle is trapped, decrease the residual waiting time
					particle[3] -= 1;
				}
				#pragma omp atomic
				mags[step] += particle[3];
				//gsl_histogram_increment (hvisits, particle[3]);
				//if (magnetization == num_particles) main_loop_break = 1;
				//int tid = omp_get_thread_num();
				//printf("Thread %i:  %i %i\n", id, i, direction);
				/*if (step%2000 == 0) {
				 printf("# Step: %8i (MAG: %5i)\r", step, magnetization);
				 fflush(stdout);
				 }*/
				//printf("%8i %8i %8i %8i\n",particle[0],particle[1],particle[2],particle[3]);
				
			} // end sub particle loop
			double stop = omp_get_wtime();
			calc_time += (stop-start);

		} // end steps loop
		/*
		 if (i%32 == 0) {
		 double stop = omp_get_wtime();
		 printf("# Particle: %8i (%8.3f s) Magnetization: %8i\r",i , (stop-start)/32 , magnetization);
		 fflush(stdout);
		 }
		 */
		// open the file we are writing to
		
		
		//#pragma omp critical
		//printf("# Particle: %8i (%8.3f s) \n",i , stop-start);		
	} // end particle loop
	printf("Speed: %.2e s/particle \n", calc_time/num_particles);
	
	FILE *outFile;
	char fname[] = "binout.omp";
	sprintf(fname, "binout.om%i",0);
	outFile = fopen(fname, "w");
	// use fwrite to write binary data to the file
	fwrite(mags, sizeof(mags[0]), nsteps, outFile);
	fclose(outFile);
	print_array(particles, 10, 3);
	
	
	//print_array(particles, num_particles, 4);
	free(mags);
	free2D_i(particles);
	free2D_i(defects);
#ifdef STATS
	printf("Directions drawn:\n");
	gsl_histogram_fprintf (stdout, h, "%g", "%g");
	printf("\n");
	gsl_histogram_free (h);
#endif
	//omp_destroy_lock(&omplock);
	return 0;
}



/***************************************************************************************************************/

/* qsort C-string comparison function */ 
int cstring_cmp(const void *a, const void *b) 
{ 
	//    const char **ia = (const char **)a;
	//    const char **ib = (const char **)b;
	//    return strcmp(*ia, *ib);
	return strcmp ( (const char*)a, (const char*)b);
	
	/* strcmp functions works exactly as expected from
	 comparison function */ 
} 


/* asm long long comparison function */ 
/*
 int asm64_comp(const void *a, const void *b) {
 int i=0;
 __asm__(
 "mov (%%rdi), %%rdx\n\t"    // Subtract low word 
 "sub (%%rsi), %%rdx\n\t" 
 "mov 8(%%rdi), %%rdi\n\t"    // Subtract high word 
 "sbb 8(%%rsi), %%rdi\n\t" 
 "sbb %%eax, %%eax\n\t"    // %eax = -1 if below, zero otherwise 
 "or %%rdx, %%rdi\n\t"    // %rdi is non-zero if comparison is non-zero 
 "neg %%rdi\n\t"    // carry flag is 1 if comparison is non-zero 
 "adc %%eax, %%eax\n\t" // Result in %eax 
 "movl %%eax, %0\n\t"
 : "=a" (i)
 :"r" (a), "r" (b)
 );
 return i;
 }
 */


int int64_cmp(const void *a, const void *b) 
{ 
	const int64_t *x = a, *y = b;
	if(*x > *y)
		return 1;
	else
		return (*x < *y) ? -1 : 0;
} 

/* qsort int comparison function */ 
int int_cmp(const void *a, const void *b) 
{ 
	//    const int *ia = (const int *)a; // casting pointer types 
	//    const int *ib = (const int *)b;
    //return *ia  - *ib; 
	/* integer comparison: returns negative if b > a 
	 and positive if a > b */ 
	return ( *(int*)a - *(int*)b );
} 

static inline int64_t hash(int x, int y, int z) {
	return  (int64_t) MULTIPLIER* (int64_t) MULTIPLIER * (int64_t) x + (int64_t) MULTIPLIER * (int64_t) y + (int64_t) z;
}


int** malloc2D_i(long nrows, long ncolumns){
	int **array = malloc(nrows * sizeof(int *));
	array[0] = malloc(nrows * ncolumns * sizeof(int));
	if (array[0] == NULL) printf("Could not allocate memory");
	for(int i = 1; i < nrows; i++)
		array[i] = array[0] + i * ncolumns;
	
	// set all elements to 0
	for (int i = 0; i < nrows; i++) {
		for (int j = 0; j < ncolumns; j++) {
			array[i][j] = 0;
		}
	}
	return array; 
}

/*
 char** malloc2D_char(long nrows, long ncolumns){
 char **array = malloc(nrows * sizeof(char *));
 array[0] = malloc(nrows * ncolumns * sizeof(char));
 if (array[0] == NULL) printf("Could not allocate memory");
 for(int i = 1; i < nrows; i++)
 array[i] = array[0] + i * ncolumns;
 return array; 
 }
 */
char** malloc2D_char(long nrows, long ncolumns){
	char **array = malloc(nrows * sizeof(char *));
	for(int i = 0; i < nrows; i++)
		array[i] = malloc(ncolumns * sizeof(char));
	return array; 
}



void free2D_i(int** array) {
	//free(&array[0]);
	free(array);
}

void print_array(int **array, int nrows, int ncolumns){
	for (int i = 0; i < nrows; i++) {
		for (int j = 0; j < ncolumns-1; j++) {
			printf("%i ",array[i][j]);
		}
		printf("%i\n",array[i][ncolumns-1]);
	}
}

void move_particle(int *particle, int direction){
	switch (direction) {
		case 0:
			particle[0] += 1;
			break;
		case 1:
			particle[0] -= 1;
			break;
		case 2:
			particle[1] += 1;
			break;
		case 3:
			particle[1] -= 1;
			break;
		case 4:
			particle[2] += 1;
			break;
		case 5:
			particle[2] -= 1;
			break;
	} // end switch statement	
}

static inline void check_pbc(int* particle, int box_size) {
	for (int i = 0; i < 3; i++) {
		// % is NOT the mod operator, but the REMAINDER, it is not working for negative numbers (of course in C only)
		//particle[i] = particle[i] % box_size + (particle[i]<0?box_size:0);
		particle[i] &= (box_size - 1);
	}
}
/* binary search */
void check_defect(int* particle, int correlation_time, int64_t* hash_list, int num_defects ){
	int64_t hash_val;
	hash_val = hash(particle[0],particle[1],particle[2]);
	int * ptr;
	ptr = bsearch( &hash_val, hash_list, num_defects , sizeof(int64_t), int64_cmp);
	if (ptr != NULL)
		particle[3] = correlation_time;
}

/* lookup table 1 */

void check_defect_hash(int* particle, int correlation_time, int64_t hash_list_min, int64_t span, char* defekt_ltb){
	int64_t hash_val, offset;
	hash_val = hash(particle[0],particle[1],particle[2]);
	offset = hash_val -  hash_list_min;
	if ((offset >= 0) && (offset < span)) {
		if (defekt_ltb[ offset ] == 1)
			particle[3] = correlation_time;
	}
}


/* check Method 3 */

void check_defect_3d(int* particle, char*** lookup, int correlation_time){
	int x = particle[0];
	int y = particle[1];
	int z = particle[2];
	if (lookup[x] != NULL) {
		if (lookup[x][y] != NULL) {
			if (lookup[x][y][z] == 1) {
				particle[3] = correlation_time;
			}
		}
	}
}

void check_defect_ltb(int* particle, int* x, int* y, int* z, int correlation_time){
	int i = particle[0] / sizeof(int);
	int bit = 1<< particle[0] % sizeof(int);
	if (  (x[i] & 1 << bit) > 0) {
		i = particle[1] / sizeof(int);
		bit = 1<< particle[1] % sizeof(int);
		if (  (y[i] & 1 << bit) > 0) {
			i = particle[2] / sizeof(int);
			bit = 1<< particle[2] % sizeof(int);
			if (  (z[i] & 1 << bit) > 0) {
				particle[3] = correlation_time;
			}
		}
	}
		/*
	 switch ( (x[particle[0] / sizeof(int)]) & (1<< particle[0] % sizeof(int))  ) {
		 case 0:
			 break;
		 default:
			 switch ( (y[particle[1] / sizeof(int)]) & (1<< particle[1] % sizeof(int))  ) {
				 case 0:
					 break;
				 default:
					 switch ( (z[particle[2] / sizeof(int)]) & (1<< particle[2] % sizeof(int))  ) {
						 case 0:
							 break;
						 default:
							 particle[3] = correlation_time;							 
					 }
			 }
	 }*/
}



/*
 void check_defect(int* particle, int correlation_time, int64_t* hash_list, int num_defects ){
 int64_t hash_val;
 hash_val = hash(particle[0],particle[1],particle[2]);
 
 
 int bsearch = 0;
 int left = 0;
 int right = num_defects-1;
 
 while (bsearch == 0 && left <= right) {
 // int middle = (left + right) / 2;
 // better: avoid integer overflow
 int middle = left + (right-left) / 2;
 
 if (hash_val == hash_list[middle]) {
 bsearch = 1;
 particle[3] = correlation_time;
 } 
 else {
 if (hash_val < hash_list[middle]) right = middle - 1;
 if (hash_val > hash_list[middle]) left = middle + 1;
 }
 }
 }
 
 */

// REFERENCE METHOD
void ref_check_defect(int* particle, int** defect_coords, int num_defects){
	int isDefect = 0; 
	for (int i = 0; (i < num_defects) && (isDefect == 0); i++) {
		for (int j=0; j<3; j++ ){
			if (particle[j] != defect_coords[i][j]) {
				break; // coordinate mismatch, go to next particle (break loop over coordinates)
			}
			else {
				if (j==2) { // x,y and z ccordinate match
					particle[3] = (int) (rexp()*3) ; // set scalar value
					isDefect = 1; // break outer loop
				}
			}
		}
	}
}




/*
 
 void HT_check_defect(int* particle, Fnv64_t* hash_list, int num_defects ){
 int* pItem;
 char hash_string[18];
 Fnv64_t hash_val;
 snprintf(hash_string, sizeof(hash_string), "%5i %5i %5i", particle[0], particle[1], particle[2]);
 hash_val = fnv_64_str(hash_string, FNV0_64_INIT);
 pItem = (int*) bsearch (&hash_val, hash_list, num_defects, sizeof (Fnv64_t), fnv64_cmp);
 if (pItem != 0) particle[3] = 1; // set scalar value
 
 }
 
 */



/*
 // now create a hashed list to find them easier (hopefully)
 Fnv64_t hash_val;
 
 Fnv64_t *hash_list = malloc( num_defects*sizeof(Fnv64_t) );
 for (int i = 0; i < num_defects; i++) {
 snprintf(hash_string, sizeof(hash_string), "%5i %5i %5i", defects[i][0], defects[i][1], defects[i][2]);
 hash_val = fnv_64_str(hash_string, FNV1_64_INIT);
 hash_list[i] = hash_val;
 }
 qsort(hash_list, num_defects,sizeof(Fnv64_t), fnv64_cmp);
 */




/* mit chars
 char **hash_list = malloc2D_char(num_defects, 18);
 //char hash_list[20][18];
 for (int i = 0; i < num_defects; i++) {
 snprintf(hash_string, sizeof(hash_string), "%5i %5i %5i", defects[i][0], defects[i][1], defects[i][2]);
 hash_list[i] = hash_string;
 printf("%03i %s\n",i, hash_list[i]);
 }
 
 
 printf("Sorted\n");
 
 qsort(hash_list, num_defects, sizeof(hash_list[0]), cstring_cmp);//cmpstring_up);
 */

