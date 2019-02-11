# scan

Convert scanned documents into PDFs where you can search for text.

Input
- PDFs
- TIFFs
- Series of TIFFs in the form of "scan-01.tiff", "scan-03.tiff",... (SimpleScan stores TIFFs like this.)

TIFFs as source produces better results than PDFs.

Install

    apt-get install imagemagick tesseract-ocr tesseract-ocr-deu

Run...

...to process *.tiff, *.pdf

    bash ocr.sh 

...to process *.tiff only

    bash ocr.sh tiff

...to process *.pdf only

    bash ocr.sh pdf

...to get a help text

    bash ocr.sh -h
