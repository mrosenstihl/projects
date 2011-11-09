/*
 *  rand_my.c
 *  RW
 *
 *  Created by Markus Rosenstihl on 28.10.11.
 *  Copyright 2011 TU Darmstadt. All rights reserved.
 *
 */

/*
 *  randtest.c
 *  RW
 *
 *  Created by Markus Rosenstihl on 28.10.11.
 *  Copyright 2011 TU Darmstadt. All rights reserved.
 *
 */


#include <time.h>
#include <stdio.h>

#include "ziggurat.h"
#include <gsl/gsl_histogram.h>

int main() {
	float test;
	clock_t start,stop;
	long long ntests  = 100000000;
	zigset(12345678);
	gsl_histogram * h = gsl_histogram_alloc (50);
	gsl_histogram_set_ranges_uniform (h, 0, 10);
	
	start = clock();
	for (long long  i = 0; i < ntests; i++) {
		test = rexp();
		gsl_histogram_increment( h, test);
	}
	stop = clock();
	gsl_histogram_fprintf (stdout, h, "%g", "%g");
	gsl_histogram_reset(h);

	
	printf("randexp: %.2e\n", (double) (stop-start) / (double) CLOCKS_PER_SEC );
	
	
	start = clock();
	for (long long  i = 0; i < ntests; i++) {
		test = rnor();
		gsl_histogram_increment( h, test);
	}
	stop = clock();
	gsl_histogram_fprintf (stdout, h, "%g", "%g");
	printf("randn: %.2e\n", (double) (stop-start) / (double) CLOCKS_PER_SEC );
	
}
