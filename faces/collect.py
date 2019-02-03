from PIL import Image
import glob, os, sys, face_recognition, itertools, subprocess, concurrent.futures, face_util

global dir_images
global dir_faces
global dir_faces_unknown
global is_verbose
global rounds_max


def print_help():
    print("Find all faces in images.")
    print("Cut each face out and store as image in './faces/unkown/")
    print(" ")
    print("Usage: ")
    print(" ")
    print("python3 collect.py -i image-dir [ -f faces-dir ] [ -r ] [ -v ] [ -h ] [ -b INTEGER ]")
    print("  -i image-dir")
    print("    Where to find the image file.")
    print("  -f faces-dir (optional)")
    print("    Where to store the faces found images.")
    print("    Default is a subdir ./faces/ that will be created if not existing.")
    print("    As a result of the script all faces found in the images")
    print("    can be found in a subdir 'unkown', e.g. './faces/unkown/'")
    print("  -r (optional)")
    print("    recursive. Traverse subdirectories of image-dir recursively.")
    print("  -v (optional)")
    print("    verbose. Prints more messages.")
    print("  -h or --help")
    print("    Print this help message.")
    print("  -b INTEGER (optional)")
    print("    Write the DB after n images are proccessed.")
    print("    When to use? To avoid errors when converting RAW to temporary JPG.")
    print("    This happens in rare cases.")
    print("    default is 0 (no effect)")
    print("    If -b is lower then 1 this parameter has no effect.")
    quit()


dir_images_arg = ""
dir_images = ""
dir_faces_arg = ""
dir_faces = ""
dir_faces_unknown = ""
next_arg = ""
is_recursive = ""
is_verbose = False
rounds_max_arg = 0
rounds_max = 0
for arg in sys.argv[1:]:
    assert isinstance(arg, object)
    if arg == '-i':
        next_arg = "-i"
    elif arg == '-f':
        next_arg = "-f"
    elif arg == '-b':
        next_arg = "-b"
    elif next_arg == '-i':
        dir_images_arg = arg
        next_arg = ""
    elif next_arg == '-f':
        dir_faces_arg = arg
        next_arg = ""
    elif next_arg == '-b':
        rounds_max_arg = arg
        next_arg = ""
    elif arg == '-r':
        is_recursive = "-r"
    elif arg == '-v':
        is_verbose = True
    elif arg == '-h' or arg == '--help':
        print_help()

dir_script = os.path.dirname(__file__)

# Check directory for images
if dir_images_arg == "":
    print("Directory for images not given as parameter. Please use '-i image-dir'.")
    print_help()

if os.path.isabs(dir_images):
    dir_images = dir_images_arg
else:
    dir_images = os.path.join(dir_script, dir_images_arg)

if not os.path.exists(dir_images):
    sys.exit("Directory for images not existing. Dir =  " + dir_images)

# Check directory for faces
if dir_faces_arg == "":
    dir_faces_arg = "faces"
    if is_verbose: print("Directory for faces not given as param. Take default dir = " + dir_faces_arg)

if os.path.isabs(dir_faces_arg):
    dir_faces = dir_images_arg
else:
    dir_faces = os.path.join(dir_script, dir_faces_arg)

if not os.path.exists(dir_faces):
    os.mkdir(dir_faces)

dir_faces_unknown = os.path.join(dir_faces, "unknown")
if not os.path.exists(dir_faces_unknown):
    os.mkdir(dir_faces_unknown)
# Prepare the 'known' to help the user where to put known faces to
dir_faces_known = os.path.join(dir_faces, "known")
if not os.path.exists(dir_faces_known):
    os.mkdir(dir_faces_known)

# Prepare the 'exclude' to help the user where to put known faces
# to exclude from beeing written to side cards or images
dir_exclude = os.path.join(dir_faces_known, "exclude")
if not os.path.exists(dir_exclude):
    os.mkdir(dir_exclude)

if is_verbose: print("max rounds for DB to store = " + str(rounds_max_arg))
try:
    rounds_max = int(rounds_max_arg)
except ValueError:    
    rounds_max = 0
    if is_verbose: print("max rounds to store DB (parameter -b) was not an integer. Take default = " + str(rounds_max))


# Start to find the images
img_dirs = []
img_dirs.append(dir_images)
if is_recursive:
    for subdir, dirs, files in os.walk(dir_images):
        for dir in dirs:
            img_dirs.append(os.path.join(subdir, dir))
for dir in img_dirs:
    face_util.collect_faces_of_dir(dir, is_verbose, True, dir_faces_unknown, rounds_max)

quit()
