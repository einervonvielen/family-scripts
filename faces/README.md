# Tag Photographs with Names of Family and Friends

This little program is for you if you want to tag photos with the names of your family and friends.

As result your friends will show up in your photographs as [tags](https://en.wikipedia.org/wiki/Exif) "Bob" and "Jane".

It is a kind of simple **Googles Picasa** but not connected to the "cloud" and completely open source.

## How to use in short

Provided you have your photographs in a directory

    ./images-dir

This directory contains your images.

Workflow in short

1. Find all faces in you photographs and write them to "unknown".

    python3 collect.py -i images-dir -r

2. Give the faces a name by manually moving them from "unkown" into "known/Bob", "known/Jane". In later rounds this script might help you

    python3 sort.py

4. The next step finds "Bob" and "Jane" in your photographs and creates a database in every directory containing you photographs. The database contains the information in what photographs "Bob" and "Jane" where found and at what position.

    python3 recognize.py -i images-dir -r

5. Write "Bob" and "Jane" into your photographs. The default is to write "face_Bob" and "face_Jane" into the side card files (*.xmp) of every photo.

    python3 write.py -i images-dir -r

### Gimmicks

Some extra features

1. This is a gimmick. It shows you all pictures of "Bob" in a HTML file and draws a rectangle around his faces

    python3 find.py -i images -p Bob

2. This is a gimmick. It shows what faces are most similar to "Bob"

    python3 compare.py -p Bob
    
### General hint for running the python scripts

Every script has a parameter "-h" to list all possible parameters.  
Examples of additional parameters might be

- '-v' verbose. Print messages what the script is doing while running
- '-r' recursive. Iterate through subdirectories of the image directory
- '-t' tolerance. Set the threshold when comparing faces (encodings)

## Tested file types and XMP files

Tested file types
- JPG
- CR2 (Canon RAW)
- DNG (Adobe RAW format used by many other manufacturers)
Many more should be possible but are not activated in the script because they are not tested yet.

Tested XMP files
- Darktable generated


## How to install

Don't give up here in case you are not used to the command line. It is no rocket science.

    git clone https://github.com/einervonvielen/import-faces.git
    su -
    cd directory-where-you-cloned-the-file-to
    bash install.sh
    
This will install
- install cmake g++ curl libboost-all-dev python3-setuptools
- download and build PIP (python packaging Manager)
- install fface_recognition including dlib (via PIP)
- install libimage-exiftool-perl ufraw-batch

For technical details see
- [face_recognition]( https://pypi.python.org/pypi/face_recognition)
- [dlib]( https://pypi.python.org/pypi/dlib)
- [exiftool]( https://de.wikipedia.org/wiki/ExifTool) and [ufraw-batch]( https://en.wikipedia.org/wiki/UFRaw)

# The Python Scripts in more detail

What you get from the python scripts

- Write persons into
  - side cards (*.xmp) or
  - the images directly
- Gimmick: Compare faces and tell how simalar they are
- Gimmick: Find persons in your image collections and show them 
  - as copied images in a special directory
  - with named frames around the faces in a web browser

## Preparation: Collect Faces

Run

    python3 collect.py -i images -r

This cuts all faces out of the images and stores them into the directory

    ./faces/unknown

## Sort Faces manually

Now create a subdir for each person

    ./faces/known/Bob
    ./faces/known/Anna

Move the 'unknown" faces, example './faces/unknown' to './faces/known/Bob'

To explicitly exclude faces move them to

    ./faces/known/exclude

## Sort Faces automatically (optional)

Run

    python3 sort.py -i images

to help you in the manual sorting process.

## Recognize Persons in your Images

Run

    python3 recognize.py -i images

This tries to find all persons (using the 'known' faces) in the image in the images directory.

## Apply Results: Write Persons to Side Cards of Images

Run

    python3 write.py -i images

Instead of writing "Bob" and "Maria" as keywords into the image directly the default behaviour of the script is to store them in a so called [side card]( https://www.darktable.org/usermanual/ch02s02s07.html.php) file. This is basically a text file with the file extension "xmp". Example: "big-party.jpg.xmp" if your image is "big-party.jpg".

Advantage: You do not touch your original image. Decent photo workflow software like [Darktable]( https://www.darktable.org) never touch the original image. Instead they store all changes into text files ("side cards") and show you a preview image only.

You probably have to tell your photo workflow software to reload the *.xmp. In Darktable you can either re-import the images or reload the XMP files the next time you start Darktable. Change the [settings]( https://www.darktable.org/usermanual/ch08s02.html.php) of Darktable.


## Apply Results: Find a Person

Run

    python3 find.py -i images -p Bob

or

    python3 find.py -i images -p Bob -p Anna

to find images only that contain both Bob AND Anna.

Run

    python3 find.py -i images -p Bob -html

to create an index.html to view the images in a browser with frames around every known person. Each frame shows the name of the person.

# Programmers Section

## The hidden 'Databases' for Faces

The scripts create some hidden files to speed up consecutive executions. They function as a kind of brain that memorizes what face was found in what image at what position.

The **"face database"**

    ./faces/.faces.db

Holds encodings of all known faces.

The **"database"(s) of faces found in a directory**

    ./images/.faces_of_dir.db
    ./images/2017/.faces_of_dir.db
    ./images/2017/big-party/.faces_of_dir.db

Holds encodings of all faces found in every image in this (sub)directory.

The **"database"(s) created by "recognize.py"**

    ./images/.faces.csv
    ./images/2017/.faces.csv
    ./images/2017/big-party/.faces.csv

Holds the information what person was found in what file at what location.
The content of this file could be like this...

    IMG_20170612_200712.jpg;2017-11-26 18:10:41.694882;1728 1542 186 186 0.13 Bob
    IMG_20170104_192421.jpg;2017-11-26 18:10:41.695723;1146 889 385 385 0.06 Bob;1060 2130 386 385 0.08 Anna


## Hints

Setting your branch to exactly match the remote branch can be done in two steps:

    git fetch origin
    git reset --hard origin/master

Befor: If you want to save your current branch's state before doing this (just in case), you can do:

    git commit -a -m "Saving my work, just in case"
    git branch my-saved-work

Commit usually

    git status
    git add --all
    git commit --all -m "Commit comment"
    git push origin master

Prepare

    git config --global user.name "name"
    git config --global user.email "name@xy.com"

8 h timeout

    git config --global credential.helper 'cache --timeout=28800'

