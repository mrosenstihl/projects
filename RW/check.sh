NUM=$1
OMP_NUM_THREADS=1 ./a.out $NUM 3000 512 10 |grep MAG
mv -v binout.omp binout.ref
OMP_NUM_THREADS=2 ./a.out $NUM 3000 512 10 |grep MAG
diff binout.ref binout.omp
rm binout.*

