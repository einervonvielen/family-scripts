from PIL import Image
import glob, os, sys, face_recognition, itertools, subprocess, concurrent.futures, numpy, face_util

global is_verbose
global known_faces
global known_encodings


def print_help():
    print(" ")
    print("Usage: ")
    print(" ")
    print("python3 sort.py [ -f faces-dir ] [ -t 0.5] [ -v ] [ -h ]")
    print("  -f faces-dir")
    print("    default = 'faces' if ommited")
    print("    Directory where to find all known and unknown faces.")
    print("    The script tries to recognize unknown faces and move")
    print("    them into the directory of the known person.")
    print("    Example: 'python sort.py faces'")
    print("      will use")
    print("      - './faces/unknown/' to find unknown faces")
    print("      - './faces/known/' to find known faces in subdirectories,")
    print("        e.g. './faces/known/Barack Obama/bigparty.jpg'")
    print("  -t 0.5 (optional)")
    print("    tolerance. Default = 0.5.")
    print("    Less then 0.6 is more strict/similar, for example 0.5")
    print("    Please refer to the documemtation of face_recognition:")
    print("    face_recognition.api.compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6)")
    print("  -v (optional)")
    print("    verbose. Prints more messages.")
    print("  -h or --help")
    print("    Print this help message.")
    print("  ")
    print("Run 'collect.py' first to find (unknown) faces in image files.")
    print("'collect.py' creates a subdirectory './faces/unknown/'.")
    print("'sort.py' will read all unknown faces from there and will move/sort.")
    print("them. Exmple './faces/known/Barack Obama/obamas_face.jpg'")
    quit()


def compare_face(file):
    unknown_img = os.path.join(dir_faces_unknown, file)
    image = face_recognition.load_image_file(unknown_img)
    img_encodings = face_recognition.face_encodings(image)
    numberofelements = len(img_encodings)
    if not numberofelements == 1:
        if is_verbose == "-v": print("WARNING: Found '" + str(numberofelements) + "' faces in file. Expected exactly  '1'. File " + unknown_img)
        return file
    nearest_face, nearest_encoding = face_util.compare_face(img_encodings[0], known_faces, known_encodings, face_tolerance, is_verbose)
    if not nearest_face == "":
        suggested_dir = os.path.join(dir_faces_suggested, nearest_face)
        if not os.path.exists(suggested_dir):
            os.makedirs(suggested_dir, exist_ok=True)
        movedfile = os.path.join(dir_faces_suggested, nearest_face, file)
        os.rename(unknown_img, movedfile)
        os.utime(movedfile)
        print(nearest_face + " < " + file)
    return file;


is_verbose = ""
dir_faces = "faces"
dir_faces_unknown = ""
dir_faces_suggested = ""
face_tolerance = 0.5
next_arg = ""
for arg in sys.argv[1:]:
    assert isinstance(arg, object)
    if arg == '-v':
        is_verbose = "-v"
    elif arg == '-f':
        next_arg = "-f"
    elif next_arg == '-f':
        dir_faces = arg
        next_arg = ""
    elif arg == '-t':
        next_arg = "-t"
    elif next_arg == '-t':
        face_tolerance = float(arg)
        next_arg = ""
    elif arg == '-h' or arg == '--help':
        print_help()

dir_script = os.path.dirname(__file__)

if not os.path.isabs(dir_faces):
    dir_faces = os.path.join(dir_script, dir_faces)

if not os.path.exists(dir_faces):
    print("Directory for faces does not exist " + dir_faces)
    print_help()

dir_faces_unknown = os.path.join(dir_faces, "unknown")
if not os.path.exists(dir_faces_unknown):
    os.mkdir(dir_faces_unknown)
    print("Directory for unknown faces does not exist. Creating dir =  " + dir_faces_unknown)
    print("There is nothing to do. The script expects pictures of unkown persons there.")
    print_help()
dir_faces_known = os.path.join(dir_faces, "known")
if not os.path.exists(dir_faces_known):
    os.mkdir(dir_faces_known)
    print("Directory for nown faces does not exist. Dir =  " + dir_faces_known)
    print("Create directories for persons, e.g. './faces/known/Obama' and move faces into it.")
    print("  './faces/known/Barack'")
    print("  './faces/known/Michelle'")
    print("... and move their faces into it.")
    print("There is nothing to do. Creating dir "+ dir_faces_known + "...")
    print_help()
dir_faces_suggested = os.path.join(dir_faces, "suggested")
if not os.path.exists(dir_faces_suggested):
    os.mkdir(dir_faces_suggested)
    print("Directory for suggested faces does not exist. Creating dir =  " + dir_faces_suggested)

# Remove empty subdirs in suggested
for subdir in os.listdir(dir_faces_suggested):
	if os.path.isdir(os.path.join(dir_faces_suggested, subdir)):
		if not os.listdir(os.path.join(dir_faces_suggested, subdir)):
			if is_verbose: print("Remove empty dir for suggested face dir " + subdir)
			os.rmdir(os.path.join(dir_faces_suggested, subdir))

# Read known faces recursivly
known_faces = []
known_encodings = []
known_faces, known_encodings = face_util.read_known_faces(dir_faces_known, is_verbose)

# Read unknown faces
files = os.listdir(dir_faces_unknown)
with concurrent.futures.ProcessPoolExecutor() as executor:
# Process the list of files, but split the work across the process pool to use all CPUs!
    for file, processed_file in zip(files, executor.map(compare_face, files)):
        if is_verbose == "-v" : print("Finished reading known face from file " + file)
