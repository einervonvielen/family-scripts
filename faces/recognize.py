from PIL import Image
import glob, os, sys, face_recognition, itertools, subprocess, concurrent.futures, face_util, datetime

global dir_images
global dir_faces
global dir_exclude_arg
global face_tolerance
global is_verbose
global is_exiftool


def print_help():
    print(" ")
    print("Recognize persons in images and store them in '.faces.csv'")
    print("1. Load known faces")
    print("2. Scan images for faces")
    print("3. Regognize a persons face")
    print("4. Write recognized persons in a hidden file for each directory")
    print("   - file name is '.faces.csv'")
    print("   - file content is 'image name;timestamp;top left bottom right person1;top left bottom right person2'")
    print(" ")
    print("Run 'find.py', 'sort.py' before.")
    print(" ")
    print("Usage: ")
    print(" ")
    print("python3 recognize.py -i image-dir [ -f faces-dir ] [ -t 0.5] [ -x ] [ -r ] [ -v ] [ -h ]")
    print("  -i image-dir")
    print("    Where to find the image file.")
    print("  -f faces-dir")
    print("    Default = './faces/' if omitted ")
    print("    Directory where to find known faces.")
    print("    The expected directory structure is")
    print("    - './faces/known/Barack Obama/'")
    print("    - './faces/known/Michelle Obama/'")
    print("  -t 0.5")
    print("    tolerance - default = 0.5.")
    print("    Less then 0.6 is more strict/similar, for example 0.5")
    print("    Please refer to the documemtation of face_recognition:")
    print("    face_recognition.api.compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6)")
    print("  -x (recommended)")
    print("    exclude - default = 'exclude'")
    print("    Example:")
    print("    If you use '-x exclude' this will exclude all faces in")
    print("    - './faces/known/exclude/'")
    print("    to be written into your side card files (or into the images)")
    print("  -r (optional)")
    print("    recursive -  traverse subdirectories of image-dir recursively.")
    print("  -v")
    print("    verbose - Prints more messages.")
    print("  -h or --help")
    print("    Print this help message.")
    quit()


def read_images(dir):
    "iterate all files of a directory"
    faces_of_dir = face_util.collect_faces_of_dir(dir, is_verbose, False, "")
    file_details = []
    for faces_of_image in faces_of_dir:
        file_detail = []
        file_detail.append(dir)
        file_detail.append(faces_of_image)
        file_details.append(file_detail)
    count_all_files = len(file_details)
    counter = 0
    if is_verbose: print("Start to recognize faces in '" + str(len(file_details)) + "' files, dir '" + dir + "'...")
    lines = ""
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Process the list of files, but split the work across the process pool to use all CPUs!
        for file_details, line in zip(file_details, executor.map(regognize_faces, file_details)):
            counter += 1            
            if not line == "":
                if is_verbose: print(str(counter) + "/" + str(count_all_files) + " known face(s) found " + line)
                print(line)
                if not lines == "":
                    lines += "\n"
                lines += line
            else:
                faces_of_image = file_details[1]
                file = faces_of_image[0]
                if is_verbose: print(str(counter) + "/" + str(count_all_files) + " no known face found in " + file)
    # store results
    if not lines == "":
        csv = os.path.join(dir, ".faces.csv")
        file = open(csv, 'w')
        try:
            file.write(lines)
        finally:
            file.close()
    return lines;


def regognize_faces(file_detail):
    dir = file_detail[0]
    faces_of_image = file_detail[1]
    ret_string = ""
    l = len(faces_of_image)
    if l < 2:
        return ret_string
    # find all (still unknown) faces in the file
    img = ""
    img_encodings = []
    face_locations = []
    counter = 0
    for part in faces_of_image:
        if counter < 1:
            img = part
        else:
            face = part
            img_encodings.append(face[0])
            face_locations.append(face[1])
        counter += 1
    numberFaces = len(img_encodings)
    d = ';%s' % datetime.datetime.now()
    ret_string += img + d
    if is_verbose: print("Found '" + str(numberFaces) + "' faces in " + img)
    was_hit = False
    face_counter = 0
    for unknown_face_encoding in img_encodings:
        nearest_face, nearest_encoding = face_util.compare_face(unknown_face_encoding, known_faces, known_encodings, face_tolerance, is_verbose)
        nearest_encoding = round(nearest_encoding, 2)
        if nearest_face == dir_exclude_arg:
            if is_verbose: print("Exclude a face found in " + img + " from beeing written. Face was found in the exclude list.")
        elif not nearest_face == "":
            face_location = face_locations[face_counter]
            top, right, bottom, left = face_location
            height = bottom - top
            width = right - left
            ret_string += ";" + str(top) + " " + str(left) + " " + str(height) + " " + str(width) + " " + str(nearest_encoding) + " " + nearest_face
            was_hit = True
        face_counter += 1
    if not was_hit:
        ret_string = ""
    return ret_string


dir_images_arg = ""
dir_images = ""
dir_faces_arg = ""
dir_faces = ""
dir_exclude_arg = "exclude"
next_arg = ""
is_recursive = False
is_verbose = False
face_tolerance = 0.5
for arg in sys.argv[1:]:
    assert isinstance(arg, object)
    if arg == '-i':
        next_arg = "-i"
    elif next_arg == '-i':
        dir_images_arg = arg
        next_arg = ""
    elif arg == '-f':
        next_arg = "-f"
    elif next_arg == '-f':
        dir_faces_arg = arg
        next_arg = ""
    elif arg == '-x':
        next_arg = "-x"
    elif next_arg == '-x':
        dir_exclude_arg = arg
        next_arg = ""
    elif arg == '-t':
        next_arg = "-t"
    elif next_arg == '-t':
        face_tolerance = float(arg)
        next_arg = ""
    elif arg == '-r':
        is_recursive = True
    elif arg == '-html':
        is_html = True
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
    dir_faces = dir_faces_arg
else:
    dir_faces = os.path.join(dir_script, dir_faces_arg)
if not os.path.exists(dir_faces):
    print("Directory for faces does not exists: " + dir_faces)
    print_help()

dir_faces_known = os.path.join(dir_faces, "known")
if not os.path.exists(dir_faces_known):
    print("Sub-Directory for faces does not exists: " + dir_faces_known)
    print_help()

dir_exclude = os.path.join(dir_faces_known, dir_exclude_arg)
if not os.path.exists(dir_exclude):
    print("Sub-Directory for faces to exclude from beeing written does not exists. Creating... " + dir_exclude)
    os.mkdir(dir_exclude)

# Read known faces recursively
known_faces = []
known_encodings = []
known_faces, known_encodings = face_util.read_known_faces(dir_faces_known, is_verbose)

# Start to find the images
img_dirs = []
img_dirs.append(dir_images)
if is_recursive:
    for subdir, dirs, files in os.walk(dir_images):
        for dir in dirs:
            img_dirs.append(os.path.join(subdir, dir))
for dir in img_dirs:
    lines = read_images(dir)
