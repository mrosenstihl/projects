#!/bin/bash
CURRENT_MAX_UID=$(dsh -c -a sh /data/markusro/scripts/get_max_uid.sh \
| awk ' $2 > maxuid  { maxuid=$2 }; END { print maxuid}')

USERNAME=$1
USERID=$(($CURRENT_MAX_UID+1))
PASSWD=$(mkpasswd -m md5)
echo "Password (encrypted): $PASSWD"
echo "$PASSWD" > /data/.tmp
echo "Creating user:"
dsh -c -M -a useradd -u $USERID -U -p \$\(cat /data/.tmp\) -m \
-G dialout,cdrom,floppy,sudo,audio,video,plugdev,netdev,powerdev $USERNAME
rm /data/.tmp
echo "Updating NIS maps..."
cd /var/yp; make; cd
