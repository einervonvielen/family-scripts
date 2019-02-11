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

TODO

- create the web page

