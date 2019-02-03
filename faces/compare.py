from PIL import Image
import glob, os, sys, face_recognition, itertools, subprocess, face_util, concurrent.futures

global dir_images
global dir_faces
global dir_exclude_arg
global face_tolerance
global is_verbose
global is_exiftool


def print_help():
    print(" ")
    print("Who is most similar to another person")
    print(" ")
    print("Usage: ")
    print(" ")
    print("python3 compare.py -p name [ -f faces-dir ] [ -x ] [ -s ] [ -v ] [ -h ]")
    print("  -p ")
    print("    person")
    print("    Print a list who is most similar to this person")
    print("    For example use-p 'Barack Obama'")
    print("    Example: -p 'Barack Obama'")
    print("    Will compare the face(s) in")
    print("    - './faces/known/Barack Obama/'")
    print("    with all other known faces")
    print("  -x (recommended)")
    print("    exclude - default = 'exclude'")
    print("    Example:")
    print("    If you use '-x exclude' this will exclude all faces in")
    print("    - './faces/known/exclude/'")
    print("    to be written into your side card files (or into the images)")
    print("  -s")
    print("    single line")
    print("    Write results into a singel line")
    print("  -v (optional)")
    print("    verbose. Prints more messages.")
    print("  -h or --help")
    print("    Print this help message.")
    quit()


def compare_face(name):
    min = 1.0
    max = 0.0
    sum = 0.0
    counter_distances = 0
    for face in known_faces:
        compare_name = face[1]
        if compare_name == name:
            # compare face encodings of person with every face encoding of known face
            compare_encoding = face[2]
            #results = face_recognition.compare_faces(person_encodings, compare_encoding)
            face_distances = face_recognition.face_distance(person_encodings, compare_encoding)
            for face_distance in face_distances:
                d = float(face_distance)
                if d < min:
                    min = d
                if d > max:
                    max = d
                sum += d
                counter_distances += 1
    average = sum / counter_distances
    result = []
    result.append(average)
    result.append(min)
    result.append(max)
    result.append(name)
    result.append(counter_distances)
    return result


person = ""
dir_faces_arg = ""
dir_faces = ""
dir_exclude_arg = "exclude"
next_arg = ""
is_verbose = ""
is_single_line = False
for arg in sys.argv[1:]:
    assert isinstance(arg, object)
    if arg == '-p':
        next_arg = "-p"
    elif next_arg == '-p':
        person = arg
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
    elif arg == '-v':
        is_verbose = "-v"
    elif arg == '-s':
        is_single_line = True
    elif arg == '-h' or arg == '--help':
        print_help()

dir_script = os.path.dirname(__file__)

# Check directory for faces
if dir_faces_arg == "":
    dir_faces_arg = "faces"
    print("Directory for faces not given as param. Take default dir = " + dir_faces_arg)
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

dir_person = os.path.join(dir_faces_known, person)
if not os.path.exists(dir_person):
    print("Sub-Directory for face '" + person + "' does not exists " + dir_person)
    print_help()

dir_exclude = os.path.join(dir_faces_known, dir_exclude_arg)
if not os.path.exists(dir_exclude):
    print("Sub-Directory for faces to exclude from beeing written does not exists. Creating... " + dir_exclude)
    os.mkdir(dir_exclude)

# Read known faces recursively
known_faces = []
known_encodings = []
known_faces, known_encodings = face_util.read_known_faces(dir_faces_known, is_verbose)

person_encodings = []
names = []
for face in known_faces:
    name = face[1]
    encoding = face[2]
    if name == person:
        person_encodings.append(encoding)
        continue
    elif name == dir_exclude_arg:
        continue
    elif not name in names:
        names.append(name)
l = len(person_encodings)
if is_verbose == "-v": print("Found and compare '" + str(l) + "' faces of person " + person)
if l < 1:
    quit("No faces found for person " + person)

results = []
with concurrent.futures.ProcessPoolExecutor() as executor:
# Process the list of files, but split the work across the process pool to use all CPUs!
    for name, result in zip(names, executor.map(compare_face, names)):
        if is_verbose == "-v": print("  to '" + name + "'")
        results.append(result)

results.sort()
s = ""
for result in results:
    if not is_single_line:
        s += "\n"
    s += result[3]
    x = str(round(result[0], 2))
    s += " (" + x
    x = str(round(result[1], 2))
    s += "/" + x
    x = str(round(result[2], 2))
    s += "/" + x
    x = str(round(result[4], 2))
    s += "/" + x + ") "
result_string = "Nearest to " + person+ ": " + s
print(result_string)