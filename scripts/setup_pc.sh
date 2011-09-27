PC=$1
scp /etc/ld.so.conf.d/acml.conf $PC:/etc/ld.so.conf.d/
scp /etc/ld.so.conf.d/atlas.conf $PC:/etc/ld.so.conf.d/
ssh $PC ldconfig
