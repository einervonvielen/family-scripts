# Creates a Web Pages from Images

Install

    apt-get install exiftool

Run (example)

    bash diary.sh images/

What it does...

The command above searches for fotos in dir "images/" and writes for each image into "content.txt"

- IMAGE:filename
- TITLE:from image with exiftool
- DESCRIPTION:from image with exiftool
- CREATE DATE:from image with exiftool
- GPS POSITION:from image with exiftool

Result

A file "content.txt". This file is loaded by diary.html. Everything else is done with JavaScript inside the web page.

Images can be of type

- JPG
- DNG
- PNG
- CR2

Exiftool can read much more file types. Adapt the script if you want more.

TODO

- create the web page

