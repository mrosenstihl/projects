CURRENT_NAME=$1
NEW_NAME=$2
PCS="
dozor
pluto
claas
dussel
alfons
mickey
goofy
"
# get the current group id
GID=$(id -g $CURRENT_NAME)
read -p "give current GID of user $CURRENT_NAME($GID):" GID
if  (( GID <= 1000 ))  
then
echo "Wrong GID"
exit 0
fi

read -p "old name: $CURRENT_NAME  new name: $NEW_NAME  GID: $GID continue? [y|n]" OK
if [[ "$OK" == [yY] ]]
then
for i in $PCS
do
echo $i
	#ssh $i "usermod -m -l $NEW_NAME -g $GID -d /home/$NEW_NAME $CURRENT_NAME;groupmod -n $NEW_NAME $CURRENT_NAME"
done
fi
