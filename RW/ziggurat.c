/* The ziggurat method for RNOR and REXP
 Combine the code below with the main program in which you want
 normal or exponential variates.   Then use of RNOR in any expression
 will provide a standard normal variate with mean zero, variance 1,
 while use of REXP in any expression will provide an exponential variate
 with density exp(-x),x>0.
 Before using RNOR or REXP in your main, insert a command such as
 zigset(86947731 );
 with your own choice of seed value>0, rather than 86947731.
 (If you do not invoke zigset(...) you will get all zeros for RNOR and REXP.)
 For details of the method, see Marsaglia and Tsang, "The ziggurat method
 for generating random variables", Journ. Statistical Software.
 *
 *
 * Fixed for 64-bit GCC March 2009 Phil Karn
 * 
 * - typdef removed
 * - using stdint.h 
 * - header file created 
 * October 2011 Markus Rosenstihl
 */



#include "ziggurat.h"
#include <math.h>

static uint32_t jz,jsr=123456789;
static int32_t hz;
static uint32_t iz, kn[128], ke[256];
static float wn[128],fn[128], we[256],fe[256];

static inline uint32_t shr3(void) {
	jz=jsr;
	jsr^=(jsr<<13);
	jsr^=(jsr>>17);
	jsr^=(jsr<<5);
	return jz+jsr;
}

static inline float uni(void){
	return .5 + (int32_t)shr3() *.2328306e-9;
}


#define RNOR (hz=shr3(), iz=hz&127, (fabs(hz)<kn[iz])? hz*wn[iz] : nfix())
#define REXP (jz=shr3(), iz=jz&255, (    jz <ke[iz])? jz*we[iz] : efix())

/* nfix() generates variates from the residue when rejection in RNOR occurs. */

float nfix(void)
{
	const float r = 3.442620f;     /* The start of the right tail */
	static float x, y;
	for(;;)
	{  x=hz*wn[iz];      /* iz==0, handles the base strip */
		if(iz==0)
		{ do{ x=-log(uni())*0.2904764; y=-log(uni());}	/* .2904764 is 1/r */
			while(y+y<x*x);
			return (hz>0)? r+x : -r-x;
		}
		/* iz>0, handle the wedges of other strips */
		if( fn[iz]+uni()*(fn[iz-1]-fn[iz]) < exp(-.5*x*x) ) return x;
		
		/* initiate, try to exit for(;;) for loop*/
		hz=shr3();
		iz=hz&127;
		if(fabs(hz)<kn[iz]) return (hz*wn[iz]);
	}
	
}

/* efix() generates variates from the residue when rejection in REXP occurs. */
float efix(void)
{ float x;
	for(;;)
	{  if(iz==0) return (7.69711-log(uni()));          /* iz==0 */
		x=jz*we[iz]; if( fe[iz]+uni()*(fe[iz-1]-fe[iz]) < exp(-x) ) return (x);
		
		/* initiate, try to exit for(;;) loop */
		jz=shr3();
		iz=(jz&255);
		if(jz<ke[iz]) return (jz*we[iz]);
	}
}
/*--------This procedure sets the seed and creates the tables------*/

/* Set up tables for RNOR */
void zigset_nor(uint32_t jsrseed)
{  const double m1 = 2147483648.0;
	double dn=3.442619855899,tn=dn,vn=9.91256303526217e-3, q;
	int i;
	
	jsr^=jsrseed;
	
	q=vn/exp(-.5*dn*dn);
	kn[0]=(dn/q)*m1;
	kn[1]=0;
	
	wn[0]=q/m1;
	wn[127]=dn/m1;
	
	fn[0]=1.;
	fn[127]=exp(-.5*dn*dn);
	
    for(i=126;i>=1;i--){
		dn=sqrt(-2.*log(vn/dn+exp(-.5*dn*dn)));
		kn[i+1]=(dn/tn)*m1;
		tn=dn;
		fn[i]=exp(-.5*dn*dn);
		wn[i]=dn/m1;
    }
}

/* Set up tables for REXP */
void zigset_exp(uint32_t jsrseed)
{  const double m2 = 4294967296.;
	double q;
	double de=7.697117470131487, te=de, ve=3.949659822581572e-3;
	int i;
	
	// doing it twice, once from zigset_exp and from zigset_nor, cancels the effect!
	//   jsr^=jsrseed; // 
	
	
	q = ve/exp(-de);
	ke[0]=(de/q)*m2;
	ke[1]=0;
	
	we[0]=q/m2;
	we[255]=de/m2;
	
	fe[0]=1.;
	fe[255]=exp(-de);
	
	for(i=254;i>=1;i--){
		de=-log(ve/de+exp(-de));
		ke[i+1]= (de/te)*m2;
		te=de;
		fe[i]=exp(-de);
		we[i]=de/m2;
	}
}
/* Set up tables */
void zigset(uint32_t jsrseed){
	zigset_nor(jsrseed);
	zigset_exp(jsrseed);
}

float rnor(){
	hz=shr3();
	iz=hz&127;
	if(fabs(hz)<kn[iz])
		return hz*wn[iz];
	else
		return nfix();
}

float rexp(){
	jz=shr3();
	iz=jz&255;
	if (jz<ke[iz])
		return jz*we[iz];
	else
		return efix();
}