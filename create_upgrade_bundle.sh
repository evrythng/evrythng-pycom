#!/bin/bash

version=$(awk -F= '/^version/{print $2}' ./version.py)
version="$(echo -e "${version}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

filename_temp=$(mktemp /tmp/firmware.XXXXXXXXX)

find . -name "*.py" -o -name "*.html" | sed -e 's,^\./,,' | tar cvf $filename_temp -T -

md5=$(md5sum $filename_temp | awk '{print $1}')

filename_final=firmware.${version}.${md5}.bin

mv $filename_temp $filename_final
