#!/bin/bash 

function sysstat {
echo -e "
#####################################################################
    Health Check Report (CPU,Process,Disk Usage, Memory)
#####################################################################

Hostname         : `hostname`(`hostname -i`)
Kernel Version   : `uname -r`
Uptime           : `uptime | sed 's/.*up \([^,]*\), .*/\1/'`
Last Reboot Time : `who -b | awk '{print $3,$4}'`
"
}

function fn_cpu_load () {
vWarnLoad=20
vCritLoad=30	
echo "	
*********************************************************************
CPU Load - > Threshold : < ${vWarnLoad} Normal, >= ${vWarnLoad} Warning , > ${vCritLoad} Critical 
*********************************************************************
"
MPSTAT=`which mpstat`
MPSTAT=$?
if [ $MPSTAT != 0 ]
then
	echo "Please install mpstat!"
else
#	echo -e ""
	vNumberCpu=`cat /proc/cpuinfo | grep ^processor | wc -l`
	
	vLoad=`cat /proc/loadavg`
	vCurrentLoad=`echo ${vLoad} | cut -d' ' -f1`
	#vCurrentLoadPerc=`echo print ${vCurrentLoad}/${vNumberCpu}.*100 | python`

	v5minLoad=`echo ${vLoad} | cut -d' ' -f2`
	#v5minLoadPerc=`echo print ${v5minLoad}/${vNumberCpu}*100 | python`

	v15minLoad=`echo ${vLoad} | cut -d' ' -f3`
	#v15minLoadPerc=`echo print ${v15minLoad}/${vNumberCpu}*100 | python`
	printf ">> Current load = %.2f \n" "$vCurrentLoad"
	printf ">> Last 5 min load = %.2f\n" "$v5minLoad"
	printf ">> Last 15 min load = %.2f\n" "$v15minLoad"
	
	vCurrentLoad=`printf "%.0f" "${vCurrentLoad}" `
	vCurrentLoadPerc=`printf "%.0f" "${vCurrentLoadPerc}" `
	printf "\nHeath Status (current load): " 
	if [[ ${vCurrentLoad} -lt ${vWarnLoad}  ]]; 
	then	
		printf "NORMAL" 
	else
		if [[ ${vCurrentLoad} -gt ${vCritLoad}  ]]; 
		then
			printf "CRITICAL"
		elif [[ ${vCurrentLoad} -gt ${vWarnLoad} ]];
		then
			printf "WARNING"
		fi	
	fi #[[ ${vCurrentLoadPerc} -lt ${vCritLoad}  ]]; 
	echo ""
	echo ""
	echo "*********************************************************************"
	echo "                    CPU Usage (Average)                                       "
	echo "*********************************************************************"
    echo "CPU | %user | %system | %iowait | %steal | %idle"
     #mpstat  | awk -v var="all" '{ if ($3 == var ) printf  "%3s | %5.2f | %7.2f | %7.2f | %6.2f | %5.2f\n", $3, $4, $5,$6,$10,$11}' 
     mpstat -P ALL | sed  '1,3d' | awk  '{ printf  "%3s | %5.2f | %7.2f | %7.2f | %6.2f | %5.2f\n", $3, $4, $5,$6,$10,$11}' 

	# 
	#i=0
	#while [ $i -lt $vNumberCpu ]
	#do
    #  mpstat -P ALL | awk -v var=$i '{ if ($3 == var ) printf  "%3d | %5.2f | %7.2f | %7.2f | %6.2f | %5.2f\n", $3, $4, $5,$6,$10,$11}' 
	#  let i=$i+1
	#done

fi

} #fn_cpu_load

function fn_processes () {
echo -e "
*********************************************************************
                             Process
*********************************************************************

=> Top memory using processs/application
`echo "PID USER %MEM TIME+ COMMAND" | awk '{printf "%6s | %-10s | %6s | %-12s | %s", $1, $2, $3, $4, $5, $6 }'`
`ps aux |  sort -rk4 | head -n 5 | awk '{ s = ""; for (i = 11; i <= NF; i++) s = s $i " "; printf "%6d | %-10s | %6s | %-6s %-5s | %s\n",$2,$1,$4,$9,$10, s }' | sed '1d' `
 
=> Top CPU using process/application
`echo "PID USER %CPU TIME+ COMMAND" | awk '{printf "%6s | %-10s | %6s | %-12s | %s", $1, $2, $3, $4, $5, $6 }'`
`ps aux |  sort -rk3 | head -n 5 | awk '{ s = ""; for (i = 11; i <= NF; i++) s = s $i " "; printf "%6d | %-10s | %6s | %-6s %-5s | %s\n",$2,$1,$3,$9,$10, s }' | sed '1d' `
"
}

function fn_disk () {
vWarn=90
vCrit=95	
echo "
*********************************************************************
Disk Usage - > Threshold < ${vWarn}% Normal > ${vWarn}% Warning > ${vCrit}% Critical
*********************************************************************
"
df -Pkh | grep -v 'Filesystem' > /tmp/df.status
echo "               MOUNT | USED  |  AVAILABLE | HEALTH STATUS"
while read DISK
do
	USAGE=`echo $DISK | awk '{print $5}' | cut -f1 -d%`
	if [ $USAGE -ge ${vCrit} ] 
	then
		STATUS='CRITICAL'
	elif [ $USAGE -ge ${vWarn} ]
	then
		STATUS='WARNING'
	else
		STATUS='NORMAL'
	fi

#	LINE=`echo $DISK | awk '{print $1,"\t",$6,"\t",$5," used","\t",$4," free space"}'`
	#LINE=`echo "${DISK} ${STATUS}" | awk '{printf "%s : %50s : %s : %s : %s", $1,$6, $5,$4,$7}'`
#	echo "${DISK} ${STATUS}" | awk '{ printf "=> Filesystem: %s\n   Mounted on: %s\n   Used: %s\n   Available: %s\n   Health Status: %s\n\n", $1,$6, $5,$4,$7}'
	echo "${DISK} ${STATUS}" | awk '{ printf "%20s | %5s | %10s | %10s\n", $6, $5,$4,$7}'

done < /tmp/df.status
rm /tmp/df.status
} #fn_disk

function fn_memory () {
### Memory
TOTALMEM=`free -m | head -2 | tail -1| awk '{print $2}'`
TOTALBC=`echo "scale=2;if($TOTALMEM<1024 && $TOTALMEM > 0) print 0;$TOTALMEM/1024"| bc -l`
USEDMEM=`free -m | head -2 | tail -1| awk '{print $3}'`
USEDBC=`echo "scale=2;if($USEDMEM<1024 && $USEDMEM > 0) print 0;$USEDMEM/1024"|bc -l`
FREEMEM=`free -m | head -2 | tail -1| awk '{print $4}'`
FREEBC=`echo "scale=2;if($FREEMEM<1024 && $FREEMEM > 0) print 0;$FREEMEM/1024"|bc -l`
TOTALSWAP=`free -m | tail -1| awk '{print $2}'`
TOTALSBC=`echo "scale=2;if($TOTALSWAP<1024 && $TOTALSWAP > 0) print 0;$TOTALSWAP/1024"| bc -l`
USEDSWAP=`free -m | tail -1| awk '{print $3}'`
USEDSBC=`echo "scale=2;if($USEDSWAP<1024 && $USEDSWAP > 0) print 0;$USEDSWAP/1024"|bc -l`
FREESWAP=`free -m |  tail -1| awk '{print $4}'`
FREESBC=`echo "scale=2;if($FREESWAP<1024 && $FREESWAP > 0) print 0;$FREESWAP/1024"|bc -l`

echo -e "
*********************************************************************
		     Memory 
*********************************************************************

=> Physical Memory
   Total = ${TOTALBC} GB
   Used  = ${USEDBC} GB
   Free  = ${FREEBC} GB
   %Free = $(($FREEMEM / $TOTALMEM * 100  ))%

=> Swap Memory
   Total = ${TOTALSBC} GB
   Used  = ${USEDSBC} GB
   Free  = ${FREESBC} GB
   %Free = $(($FREESWAP * 100 / $TOTALSWAP  ))%
"
} # fn_memory

sysstat
fn_cpu_load
fn_processes
fn_disk
fn_memory

