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
#include "ziggurat.h"

//#define STATS
#define MULTIPLIER 1000000  // seperates the coordiantes (poor man's hash)




int main (int argc, char * argv[]) {
	int num_particles = 1024*1024;
	int num_defects = 1024*32;
	int box_size = 512;
	long long nsteps = 15;
	double start,stop;
	
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
	
	
	zigset(1);
	dsfmt_t dsfmt;
	
	int seed = 0;
	int  *mags = malloc(nsteps * sizeof(int)); // magnetization per step
	int  *correlation_times = malloc(num_particles * sizeof(int)); // random distribution of correlation times
	
	int **particles = malloc2D_i(num_particles, 4); // 2d array for particles: x,y,z,mag
	int **defects = malloc2D_i(num_defects, 3); // 2d array for defect coordinates
	
	//int *particle;
	//int direction;
	
	double *random_numbers = malloc(num_particles * sizeof(double));
	
	// init random number generator
	dsfmt_init_gen_rand(&dsfmt, seed);
	
	// check if we can create the hashes
	assert(box_size < MULTIPLIER);
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
	// Information:
	printf("#-------------------- Paramters --------------------\n");
	printf("# Particles: %i\n", num_particles);
	printf("# Box size: %i\n", box_size);
	printf("# Defects: %i (Density: %.2e)\n", num_defects, (float) num_defects/pow(box_size,3) );
	printf("# Steps: %lli\n", nsteps);
	printf("#---------------------------------------------------\n");
	printf("\n# Starting ...\n");
	
	// distribute particles from 0 to +box_size
	for (int j = 0; j < 3; j++) {
		// create random numbers for the positions
		dsfmt_fill_array_open_close(&dsfmt, random_numbers, num_particles);
		// scale to boxsize
		for (int i=0 ;i < num_particles; i++) {
			random_numbers[i] *= box_size;
			particles[i][j] = (int) random_numbers[i];
		}
	}
	
	
	// distribute defects from 0 to +box_size
	for (int j = 0; j < 3; j++) {
		for (int i=0 ; i < num_defects; i++) {
			int val = (int) (dsfmt_genrand_open_close(&dsfmt)*box_size);
			defects[i][j] = val;
		}
	}
	
	// now create a hashed list to find them easier (hopefully)
	int64_t *hash_list = malloc( num_defects*sizeof(int64_t) );
	for (int i = 0; i < num_defects; i++) {
		hash_list[i] = hash(defects[i][0],defects[i][1],defects[i][2]);
	}
	
	
	qsort(hash_list, num_defects, sizeof(int64_t), int64_cmp);
	
	
	// main loop
	int main_loop_break = 0;
	for (int step = 0; step < nsteps && main_loop_break ==0; step++) {
		start = 0; //omp_get_wtime();
		int magnetization = 0;
		// create random numbers for the movements (directions 1..6)
		dsfmt_fill_array_open_close(&dsfmt, random_numbers, num_particles);
#pragma omp parallel sections 
		{
#pragma omp section
			{
				// scale the to 0,1,2,3,4,5 (the 6 directions)
				for (int i=0 ;i < num_particles; i++) {
					random_numbers[i]*=6;
				}
			}
#pragma omp section
			{
				// rdistribution of correlation times, rexp,rnor are NOT thread safe!
				for (int i=0 ;i < num_particles; i++) {
					correlation_times[i] = (int) rexp()*30;
				}
			}
		}
		
		// loop over particles
		
		//		#pragma omp parallel  // shared(random_numbers,particles,hash_list,num_defects,step)
		//		{
#pragma omp parallel for schedule(dynamic,256) reduction(+:magnetization)// private(j) um j privat zu halten falls wir eine zweite for schleife hätten
		for (int i = 0; i < num_particles; i++) {
			// int tid = omp_get_thread_num();
			// int num_threads = omp_get_num_threads();
			
			int* particle = particles[i];
			int direction = (int) random_numbers[i];
			
			// only move particles which have not met defect yet == 0
			// or see how often they met a defefct >= 0
			if (particle[3] == 0) { 
#ifdef STATS
				// update histogram
				//#pragma  omp critical
				gsl_histogram_increment (h, direction);
#endif
				//if (step == 10 && i==10) printf("%i %i %i\n",particle[0],particle[1],particle[2]);
				
				// random step
				move_particle(particle, direction);
				
				// obey periodic boundary conditions, i.e. fold back
				check_pbc(particle, box_size);
				
				int tc = correlation_times[i];
				check_defect(particle, tc , hash_list, num_defects);
//				ref_check_defect(particle, defects, num_defects);
				
			}
			else { // particle is trapped, decrease the residual waiting time
				particle[3] -= 1;
				magnetization += 1;//particle[3];
			}
			//gsl_histogram_increment (hvisits, particle[3]);
			//if (magnetization == num_particles) main_loop_break = 1;
			//int tid = omp_get_thread_num();
			//printf("Thread %i:  %i %i\n", id, i, direction);
		} // end particle loop
		
		double dist = 0;
#pragma omp parallel for reduction(+:dist)
		for (int i = 0; i < num_particles; i++) {
			dist += sqrt(pow(box_size/2 - particles[i][0],2) + pow(box_size/2 - particles[i][1],2) + pow(box_size/2 - particles[i][2],2))  ;
		}
		dist /= num_particles;
		
#ifdef STATS
		if (step%5 == 0) {
			/*
			 char fname[100];
			 snprintf(fname, sizeof(fname), "data/dist_step%05i.dat", step);
			 FILE *fp = fopen(fname, "w");
			 gsl_histogram_fprintf(fp, hvisits, "%g", "%g");
			 fclose(fp);
			 */
		}
		gsl_histogram_reset(hvisits);
#endif
		mags[step] = magnetization;
		stop = 0;//omp_get_wtime();
		printf("# Step: %8i (MSD: %e, MAG: %i) est. runtime: %.0f min %.0f s\r", \
			   step, dist, magnetization, (stop-start)/60 * (nsteps - step), (stop-start) * (nsteps - step));
		fflush(stdout);
		
	} // end steps loop
	printf("\n# Simulation finnished\n");
	
	FILE *outFile;
	// open the file we are writing to
	if(!(outFile = fopen("binout.omp", "w")))
		return 1;
	
	// use fwrite to write binary data to the file
	fwrite(mags, sizeof(mags[0]), nsteps, outFile);
	fclose(outFile);
	
	
	/*
	 for (int i = 0; i < num_particles; i++) {
	 if (particles[i][3] == 1) printf("%i\n", i);
	 }
	 */
	
	
	
	//print_array(particles, num_particles, 4);
	
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

void check_pbc(int* particle, int box_size) {
	for (int i = 0; i < 3; i++) {
		
		// % is NOT the mod operator, but the REMAINDER, it is not working for negative numbers (of course in C only)
		particle[i] = particle[i] % box_size + (particle[i]<0?box_size:0);		
	}
}

void check_defect(int* particle, int correlation_time, int64_t* hash_list, int num_defects ){
	int64_t hash_val;
	hash_val = hash(particle[0],particle[1],particle[2]);
	int * ptr;
	ptr = bsearch( &hash_val, hash_list, num_defects , sizeof(int64_t), int64_cmp);
	if (ptr != NULL)
		particle[3] = correlation_time;
}

/*
void check_defect(int* particle, int correlation_time, int64_t* hash_list, int num_defects ){
	int64_t hash_val;
	hash_val = hash(particle[0],particle[1],particle[2]);
	
	
	int bsearch = 0;
	int left = 0;
	int right = num_defects-1;
	
	while (bsearch == 0 && left <= right) {
		int middle = (left + right) / 2;
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

// REFERENZ IMPLEMENTIERUNG
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

