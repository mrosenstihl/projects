LD_LIBRARY_PATH="./dSFMT-src-2.1:./zmq/lib:/opt/local/lib"
CFLAGS=-I/opt/local/include/gsl -I./zmq/include
LDFLAGS=-lgsl -L./zmq/lib
STDFLAGS=-g -Wall -pedantic --std=c99  -D DSFMT_MEXP=19937 -D HAVE_SSE2=1
OPT=-O3 -mtune=core2 -ftree-vectorizer-verbose=1 -msse2
DEBUG=-O0 
OPENMP=-fopenmp
GCC=/opt/local/bin/gcc-mp-4.6 
all: rw
rw:	main.o ziggurat.o dSFMT.o
	$(GCC) $(OPENMP) main.o dSFMT.o ziggurat.o -o rw
main.o:	main.c
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) -c main.c
ziggurat.o:	ziggurat/ziggurat.c
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) -c  ziggurat/ziggurat.c

dSFMT.o:	dSFMT-src-2.1/dSFMT.c
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) -c dSFMT-src-2.1/dSFMT.c
debug:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(DEBUG) $(LDFLAGS) $(OPENMP) main.c dSFMT-src-2.1/dSFMT.c ziggurat/ziggurat.c -o rw

zigtest:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) ziggurat/zigtest.c ziggurat/ziggurat.c  -lm  -o ziggurat/zigtest
clean:
	rm rw *.o
check:
	OMP_NUM_THREADS=1 ./rw 262144 1024 512 64 |grep MAG
	mv binout.omp binout.ref
	OMP_NUM_THREADS=2 ./rw 262144 1024 512 64 |grep MAG
	diff binout.ref binout.omp 
	#/bin/test "$$?" -eq 0
	#echo "Program not threadsave!"
	rm binout.*
rw0mq:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) zmq_main.c  -lzmq dSFMT-src-2.1/dSFMT.c ziggurat/ziggurat.c -o rw0mqs
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) zmq_worker.c  -lzmq dSFMT-src-2.1/dSFMT.c ziggurat/ziggurat.c -o rw0mqw
	
