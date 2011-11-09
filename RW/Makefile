LD_LIBRARY_PATH="./dSFMT-src-2.1:./zmq/lib:/opt/local/lib"
CFLAGS=-I/opt/local/include/gsl -I./zmq/include
LDFLAGS=-lgsl -L./zmq/lib
STDFLAGS=-g -Wall -pedantic --std=c99  -D DSFMT_MEXP=19937
OPT=-O3 -mtune=core2
DEBUG=-O0
OPENMP=-fopenmp
GCC=/opt/local/bin/gcc-mp-4.6 
all: rw zigtest
rw:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) main.c dSFMT-src-2.1/dSFMT.c ziggurat.c -o rw
rw0mq:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) zmq_main.c  -lzmq dSFMT-src-2.1/dSFMT.c ziggurat.c -o rw0mqs
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) $(OPENMP) zmq_worker.c  -lzmq dSFMT-src-2.1/dSFMT.c ziggurat.c -o rw0mqw
debug:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(DEBUG) $(LDFLAGS) $(OPENMP) main.c dSFMT-src-2.1/dSFMT.c ziggurat.c -o rw

zigtest:
	$(GCC) $(STDFLAGS) $(CFLAGS) $(OPT) $(LDFLAGS) zigtest.c ziggurat.c  -lm  -o zigtest
clean:
	rm zigtest rw
check:
	OMP_NUM_THREADS=1 ./rw 262144 1024 512 64 |grep MAG
	mv binout.omp binout.ref
	OMP_NUM_THREADS=2 ./rw 262144 1024 512 64 |grep MAG
	diff binout.ref binout.omp
	rm binout.*
	
