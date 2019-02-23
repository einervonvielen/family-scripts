#!/bin/bash
# apt-get install exiftool


if type exiftool >/dev/null 2>&1 ; then
	echo "ok, exiftool is installed"
else
	echo "Install apt-get install exiftool"
	exit
fi


if [ "$1" == "-h" ]; then
	echo "Create a HTML page (diary) from images"
	echo "You can use one of the following parameters"
	echo " "
	echo "  path to image directory"
	echo "       example: diary.sh images/another-subdir/"
	echo " "
	echo " "
	echo "  -h   ... show this help message"
	echo "       example: diary.sh -h"
	exit
fi

if [ -z "$1" ]; then
	imgdir='.'
else
	imgdir=$1
	imgdir=$(echo $imgdir | sed 's:/*$::')
fi
echo "image directory is: $imgdir"

outfile="diary.html"
echo "" > $outfile
shopt -s nullglob
for file in "$imgdir"/*.{jpg,JPG,jpeg,JPEG,png,PNG,dng,DNG,cr2,CR2} ; do
	content+="<p>\n"
	echo "# $file"
	lines=$(exiftool "$file")
	# echo "lines: $lines"
	title=""
	description=""
	creation_date=""
	gps_position=""
	while read -r line; do
		key="$( cut -d ':' -f 1 <<< "$line")"
		key="$(echo "$key" | xargs)"
		key="${key,,}"
		#echo "key is not lower case: $key"
		value="$( cut -d ':' -f 2- <<< "$line")"
		#echo "key is:-$key-"
		if [ "$key" = "title" ]; then
			title="$value"
		fi
		if [ "$key" = "description" ] || [ "$key" = "image description" ]; then
			description="$value"
		fi		
		if [ "$key" = "create date" ] ; then
			creation_date="$value"
		fi		
		if [ "$key" = "gps position" ] ; then
			gps_position="$value"
		fi	
	done <<< "$lines"
	if [ "$title" != "" ]; then
		echo "TITLE:$title"
		content+="<div class='title'>$title</div>\n"
	fi
	content+="<img src='$file'>\n"
	if [ "$creation_date" != "" ]; then
		echo "CREATION DATE:$creation_date"
		content+="<div class='date'>$creation_date</div>\n"
	fi
	if [ "$gps_position" != "" ]; then
		echo "GPS POSITION:$gps_position\n"
		content+="<div class='position'>$gps_position</div>\n"
	fi
	if [ "$description" != "" ]; then
		echo "DESCRIPTION:$description"
		content+="<div class='description'>$description</div>\n"
	fi
	content+="</p>\n"
done

read -r -d '' html <<- EOM
<html>
<head>
<meta charset="utf-8"/>
<style>
img {width:100%}
.title {font-size:2.5em}
</style>
</head>
<body>
diary
</body>
</html>
EOM

echo -e "${html/diary/$content}" >> $outfile

