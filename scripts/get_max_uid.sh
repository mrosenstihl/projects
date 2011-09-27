awk -F: '($3>=1000) && ($1!="nobody" && $3<60000) &&  ($3 > maxuid)  { maxuid = $3;maxuser=$1 } ; END { print maxuser " "  maxuid }' /etc/passwd
