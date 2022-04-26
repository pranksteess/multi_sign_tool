#!/bin/bash
root_dir=`pwd`
file_name="multi_sign_server.py"
log_name="run.log"
count=`ps aux|grep multi_sign_server|grep -v "grep"`
if [ "$?" != "0" ]; then
	echo "no pid, will run it"
	(nohup python3 -u ${root_dir}/${file_name} > ${root_dir}/${log_name} 2>&1 &)
else
	echo "running"
fi
