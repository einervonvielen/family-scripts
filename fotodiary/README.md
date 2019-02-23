# Creates a Web Pages from Images

Install

    apt-get install exiftool

Run (example)

    bash diary.sh images/

Result

    diary.html

What the script does...

The command above searches for fotos in dir "images/" and reads in every image

- TITLE:from image with exiftool
- DESCRIPTION:from image with exiftool
- CREATE DATE:from image with exiftool
- GPS POSITION:from image with exiftool

Images can be of type

- JPG
- DNG
- PNG
- CR2

Exiftool can read much more file types. Adapt the script if you want more.

