#!/bin/bash
# apt-get install imagemagick tesseract-ocr tesseract-ocr-deu

function check {
	if type convert ; then
		echo "Yes, convert is installed"
	else
		echo "Install apt-get install imagemagick"
		exit
	fi
	if type tesseract ; then
		echo "Yes, tesseract-ocr is installed"
	else
		echo "Install apt-get install tesseract-ocr"
		exit
	fi
}

function prepare {
	if [ ! -d "$ocrdir" ]; then
		mkdir -p "$ocrdir"
	fi
	if [ ! -d "$originalsdir" ]; then
		mkdir -p "$originalsdir"
	fi
	if [ ! -d "$backupdir" ]; then
		mkdir -p "$backupdir"
	fi
	rm -f tmp.tiff
}

function pdf {
	count=`ls -1 *.pdf 2>/dev/null | wc -l`
	if [ $count != 0 ]
	then 
		echo "Converting all PDFs into searchable PDFs..."
		for fullfile in *.pdf
		do
			echo "Original is PDF: $fullfile"
			echo "++ Converting $fullfile --> tmp.TIFF"
			convert -density 300 "$fullfile" -depth 8 -strip -background white -alpha off tmp.tiff
			filename=$(basename -- "$fullfile")
			#extension="${filename##*.}"
			filename="${filename%.*}"
			resultfile="$ocrdir/$filename"
			echo "++ Converting tmp.TIFF --> searchable PDF = $resultfile"
			tesseract tmp.tiff -l deu "$resultfile" pdf txt
			if [ $? -eq 0 ]; then
				rm -f tmp.tiff
				mv $fullfile "$originalsdir/$fullfile"
			else
				exit
			fi
		done
	else
		echo "No PDFs found."
	fi 
}

function tiff {
	count=`ls -1 *.tiff 2>/dev/null | wc -l`
	if [ $count != 0 ]
	then 
		echo "Converting all TIFFs into searchable PDFs..."
		for fullfile in *.tiff
		do
			if [ -f "$fullfile" ]; then
				echo "Orignal is TIFF: $fullfile"
				ocrfilename="$ocrdir/$fullfile"
				filename=$(basename -- "$fullfile")
				filename="${filename%.*}"
				if [[ "$filename" =~ ^(.*)(-[0-9]{1,2})$ ]]; then
					filenamestart="${BASH_REMATCH[1]}"
					concatedTIFF="$filenamestart.tiff"
					resultfile="$ocrdir/$filenamestart"
					echo "Concatenating TIFFs beginning with $filenamestart to $concatedTIFF"
					convert $filenamestart-* "$concatedTIFF"
					if [ $? -eq 0 ]; then
						mv $filenamestart-* $backupdir
					else
						echo "Failed to concatenate TIFFs. Exit value was $?"
						rm -f $concatedTIFF
						exit 1
					fi
					echo "++ Converting  $concatedTIFF --> searchable PDF = $resultfile"
					tesseract $concatedTIFF -l deu "$resultfile" pdf txt
					mv $concatedTIFF "$originalsdir/$concatedTIFF"
				else
					resultfile="$ocrdir/$filename"
					echo "++ Converting  $fullfile --> searchable PDF = $resultfile"
					tesseract $fullfile -l deu "$resultfile" pdf txt
					mv $fullfile "$originalsdir/$fullfile"				
				fi
			fi
		done
	else
		echo "No TIFFs found."
	fi 
}

# convert -density 300 /path/to/my/document.pdf -depth 8 -strip -background white -alpha off file.tiff
# tesseract file.tiff -l deu out pdf txt

ocrdir="ocr";
originalsdir="sources/originals"
backupdir="sources/tiff"

check
prepare

if [ "$1" == "pdf" ]; then
	pdf
elif [ "$1" == "tiff" ]; then
	tiff
elif [ "$1" == "-h" ]; then
	echo "Create text-searchable PDFs from PDFs and TIFFs"
	echo "You can use one of the following parameters"
	echo " "
	echo "  pdf  ... convert all PDFs into searchable PDFs"
	echo "       example: ocr.sh pdf"
	echo " "
	echo "  tiff ... convert all TIFFs into searchable PDFs"
	echo "       example: ocr.sh tiff"
	echo "       The script concatenates TIFFs like a-1.tiff, a-2.pdf,..."
	echo "       automatically into a single TIFF and this one in a single PDF."
	echo " "
	echo "  -h   ... show this help message"
	echo "       example: ocr.sh -h"
else
	tiff
	pdf
fi



