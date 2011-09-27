CURRENT_MAX_UID=$(dsh -c -a sh /data/markusro/scripts/get_max_uid.sh \
| awk ' $2 > maxuid  { maxuid=$2 }; END { print maxuid}')
echo $CURRENT_MAX_UID
