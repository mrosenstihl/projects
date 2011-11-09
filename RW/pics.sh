for i in data/*.dat
do
echo "$i\r"
gnuplot << EOT
set term png
set output "pics/$(basename $i).png"
plot [0:1000][0:1500] '$i' using 1:3:(1) w boxes fs solid 0.7
EOT
done
