/*
 *  ziggurat.h
 *  RW
 *
 *  Created by Markus Rosenstihl on 28.10.11.
 *  Copyright 2011 TU Darmstadt. All rights reserved.
 *
 */

#include <stdint.h>

typedef unsigned int uint32;
typedef signed int int32;

void zigset(uint32_t jsrseed);
float rnor(void);
float rexp(void);