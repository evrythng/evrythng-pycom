#!/bin/bash

version=$(awk -F= '/^version/{print $2}' ./version.py)
version="$(echo -e "${version}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

filename_temp=$(mktemp /tmp/firmware.XXXXXXXXX)

find . -name "*.py" -o -name "*.html" | sed -e 's,^\./,,' | tar cvf $filename_temp -T -

machine=`uname`
if [ "$machine" == "Linux" ]; then
    md5=$(md5sum $filename_temp | awk '{print $1}')
elif [ "$machine" == "Darwin" ]; then
    md5=$(md5 $filename_temp | awk -F= '{print $2}' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
else
    echo "$machine system is not supported"
    exit 1
fi

filename_final=firmware.${version}.${md5}.bin

mv $filename_temp $filename_final
