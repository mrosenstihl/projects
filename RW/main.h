/*
 *  main.h
 *  RW
 *
 *  Created by Markus Rosenstihl on 23.10.11.
 *  Copyright 2011 TU Darmstadt. All rights reserved.
 *
 */
#include <stdint.h>

int cstring_cmp(const void *a, const void *b);

int int64_cmp(const void *a, const void *b);

int int_cmp(const void *a, const void *b);

static inline int64_t hash(int x, int y, int z);

int** malloc2D_i(long nrows, long ncolumns);

void free2D_i(int** array);

void print_array(int **array, int nrows, int ncolumns);

void move_particle(int *particle, int direction);

void check_pbc(int* particle, int box_size);

void ref_check_defect(int* particle, int** defect_coords, int num_defects);

void check_defect(int* particle, int correlation_time, int64_t* hash_list, int num_defects );
void check_defect_tlb(int* particle, int correlation_time, int64_t hash_list_min, int64_t span, char* defekt_ltb);
void check_defect_3d(int* particle, char*** lookup, int correlation_time);
char** malloc2D_char(long nrows, long ncolumns);

