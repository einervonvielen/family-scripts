from PIL import Image
import glob, os, sys, itertools, subprocess, concurrent.futures, face_util

global dir_images
global dir_faces
global dir_exclude_arg
global face_tolerance
global is_verbose
global is_exiftool


def print_help():
    print(" ")
    print("Write recognized persons into")
    print("- the side card files")
    print("- the images directly (use param '-e')")
    print(" ")
    print("Steps")
    print("1. Read the hidden file '.faces.csv' in a (sub)directory")
    print("2. Write the persons to")
    print("   - side card files *.XMP (tested for Darktable)")
    print("   - image files directly (using 'exiftool')")
    print(" ")
    print("Usage: ")
    print(" ")
    print("python3 write.py -i image-dir [ -r ] [ -e ] [ -n ] [ -m ] [ -v ] [ -h ]")
    print("  -i image-dir")
    print("    Where to find the image file.")
    print("  -r (optional)")
    print("    recursive -  traverse subdirectories of image-dir recursively.")
    print("  -e (optional)")
    print("    e - exiftool")
    print("    Write the names of faces into the image file directly.")
    print("    In any case the faces are written into the XMP file (side card),")
    print("  -n (optional)")
    print("    n - no prefix 'face'")
    print("    A person 'Bob' will be written as 'face Bob' into the XMP or image.")
    print("    To omit the prefix 'face ' use the parameter '-n'.")
    print("  -m (optional)")
    print("    m - multicore")
    print("    Use all cores of the CPU. (Sometimes this seems to be not stable.)")
    print("  -v (optional)")
    print("    verbose. Prints more messages.")
    print("  -h or --help")
    print("    Print this help message.")
    quit()


def write_images(dir):
    csv_file = os.path.join(dir, ".faces.csv")
    if not os.path.exists(csv_file):
        return
    global current_dir
    current_dir = dir
    input = open(csv_file, 'r')
    lines = input.read().splitlines()
    input.close()
    l = len(lines)
    if is_verbose: print("Start to write persons to '" + str(l) + "' files. Dir is " + dir + "...")
    if not is_multicore:
        for line in  lines:
            write_image(line)
    else:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Process the list of files, but split the work across the process pool to use all CPUs!
            for file, infile in zip(lines, executor.map(write_image, lines)):
                # if is_verbose: print("Finished " + file)
                return


def write_image(line):
    details = face_util.read_faces_csv_line(line)
    file_name = details[0]
    path = os.path.join(current_dir, file_name)
    if not os.path.exists(path):
        return ""
    boxes = details[2]
    for box in boxes:
        # Write to XMP
        # path, person, similarity
        subject = box[0]
        if not is_no_prefix:
            subject = "face " + subject
        write_faces(path, subject, box[5])
        # Write to image directly
        if is_exiftool:
            # write face to image file directly
            write_face_to_img(path, subject, box[5])
    return path


def write_faces(img, subject, similarity):
    # writ face to side card file (XMP) in any case
    xmp_file, lines = write_face_to_xmp(img, subject, similarity)
    size = len(lines)
    if size > 0:
        content = ""
        for line in lines:
            if not content == "":
                content += "\n"
            content += str(line)
        xmp_file = open(xmp_file, 'w')
        try:
            xmp_file.write(content)
        finally:
            xmp_file.close()


def write_face_to_img(img, name, nearest_encoding):
    "Write a face into the image"
    print("'" + name + "' (similarity " + str(nearest_encoding) + ") > " + img)
    # exiftool - m - overwrite_original - subject -= "$name" - subject += "$name" "$img"
    return_code = subprocess.call(["exiftool", "-m", "-overwrite_original", "-subject-=" + name, "-subject+=" + name, img])
    if not return_code == 0:
        if is_verbose: print("WARNING: Return code of exiftool " + str(return_code) + " is not '0' for face " + name + " and image + " + img)
    return


def write_face_to_xmp(img, name, nearest_encoding):
    "Write a face into the side card file *.xmp"
    lines = []
    xmp_file = img + ".xmp"
    # 1. Check wether XMP file exists
    #    If not > return
    if not os.path.exists(xmp_file):
        if is_verbose: print("'" + name + "' (similarity " + str(nearest_encoding) + ") not written to side card file (XMP). File does not exist " + xmp_file)
        return xmp_file, lines
    # 2. Check if the face does exists as subject already
    #    If yes > do nothing > return
    #    Make sure the name is found in the element <dc:subject> and not for example in <dc:creator>
    line_search_subject = "<rdf:li>" + name + "</rdf:li>"
    line_search_subject_s = "<dc:subject>"
    line_search_subject_e = "</dc:subject>"
    line_search_h_subject_s = "<lr:hierarchicalSubject>"
    line_search_h_subject_e = "</lr:hierarchicalSubject>"
    line_count_subject = 0
    line_count_h_subject_s = 0
    line_count_h_subject_e = 0
    counter = 0
    f = open(xmp_file, 'r')
    try:
        content = f.read()
    finally:
        f.close()
    lines = content.split("\n")
    for line in lines:
        if line_search_subject in line:
            line_count_subject = counter
        if line_search_subject_s in line:
            line_count_subject_s = counter
        if line_search_subject_e in line:
            line_count_subject_e = counter
        if line_search_h_subject_s in line:
            line_count_h_subject_s = counter
        if line_search_h_subject_e in line:
            line_count_h_subject_e = counter
        counter += 1
    if line_count_subject > 0:
        # Found name. Check if really is inside a subject or hierarchicalSubject
        if line_count_subject_s < line_count_subject and line_count_subject_e > line_count_subject:
                print("'" + name + "' (similarity " + str(nearest_encoding) + ") = " + xmp_file)
                return xmp_file, lines
        if line_count_h_subject_s < line_count_subject and line_count_h_subject_e > line_count_subject:
                print("'" + name + "' (similarity " + str(nearest_encoding) + ") = " + xmp_file)
                return xmp_file, lines
    # 3. Check if at least one subject does exits already
    #    If yes > add the face as subject to
    #    - <dc:subject>
    #    - <lr:hierarchicalSubject>
    #      Darktable 2.2.1 will automatically create it
    line_search_subject = "<dc:subject>"
    line_search_hierarchicalSubject = "<lr:hierarchicalSubject>"
    line_count_subject = 0
    line_count_hierarchicalSubject = 0
    line_count = 0
    for line in lines:
        if line_search_subject in line:
            line_count_subject = line_count
        if line_search_hierarchicalSubject in line:
            line_count_hierarchicalSubject = line_count
        line_count += 1
    if line_count_subject > 0:
        # other subjects (may be names) are found. Add the name.
        newline = "     <rdf:li>" + name + "</rdf:li>"
        lines.insert(line_count_subject + 2, newline)
        if line_count_hierarchicalSubject > 0:
            newline = "     <rdf:li>" + name + "</rdf:li>"
            lines.insert(line_count_hierarchicalSubject + 3, newline)
        print("'" + name + "' (similarity " + str(nearest_encoding) + ") > " + xmp_file)
        return xmp_file, lines
    # Result so far: No subject was found.
    # IMPORTANT: at least for XMP generated by darktable:
    #            Watch the existance and order of name spaces in the attributes
    #            as attributes of the XML element description.
    #            Example: xmlns:dc="http://purl.org/dc/elements/1.1/"
    # 4. Check it at least one XML element <dc:XYZ> does exist for xmlns:dc="http://purl.org/dc/elements/1.1/"
    #    If yes > create element <dc:subject> for face and insert after last element <dc:XYZ>
    #             There seems to be no reason to create and insert <lr:hierarchicalSubject> too (testet Dar
    line_search_dc = "</dc:"
    line_search_xmlns = "xmlns:darktable"
    line_search_darktable = "</darktable:"
    line_found_dc = 0
    line_found_xmlns = 0
    line_found_darktalble = 0
    counter = 0
    for line in lines:
        if line_search_dc in line:
            line_found_dc = counter
        if line_search_xmlns in line:
            line_found_xmlns = counter
        if line_search_darktable in line:
            line_found_darktalble = counter
        counter += 1
    if line_found_dc > 0:
        # Yes <dc:XYZ> was found. Create <dc:subject> and insert face
        lines = insert_face_in_XMP(name, lines, line_found_dc + 1)
    else:
        # 5. No element <dc:XYZ> was found.
        #    - insert namespace as attribute
        #    - insert face
        if line_found_xmlns > 0:
            lines.insert(line_found_xmlns + 1, '    xmlns:dc = "http://purl.org/dc/elements/1.1/"')
            if line_found_darktalble > 0:
                lines = insert_face_in_XMP(name, lines, line_found_darktalble + 2)
            else:
                print("WARNING: Failed to insert '" + name + "' in XMP. Reason: Something unexpected happened. Found no attribute 'xmlns:darktable' to insert 'xmlns:dc' after it. This is needed to insert face in " + xmp_file)
                lines = []
        else:
            print("WARNING: Failed to insert '" + name + "' in XMP. Reason: Something unexpected happened. Found no (closed) element '</darktable>' to insert face after it in " + xmp_file)
            lines = []
    print("'" + name + "' (similarity " + str(nearest_encoding) + ") >> " + xmp_file)
    return xmp_file, lines


def insert_face_in_XMP(name, lines, index):
    newlines = []
    newlines.append("   <dc:subject>")
    newlines.append("    <rdf:Seq>")
    newlines.append("     <rdf:li>" + name + "</rdf:li>")
    newlines.append("    </rdf:Seq>")
    newlines.append("   </dc:subject>")
    for newLine in newlines:
        lines.insert(index, newLine)
        index += 1
    return lines


dir_images_arg = ""
dir_images = ""
next_arg = ""
is_recursive = False
is_verbose = False
is_exiftool = False
is_no_prefix = False
is_multicore = False
for arg in sys.argv[1:]:
    assert isinstance(arg, object)
    if arg == '-i':
        next_arg = "-i"
    elif next_arg == '-i':
        dir_images_arg = arg
        next_arg = ""
    elif arg == '-r':
        is_recursive = True
    elif arg == '-e':
        is_exiftool = True
    elif arg == '-m':
        is_multicore = True
    elif arg == '-v':
        is_verbose = True
    elif arg == '-n':
        is_no_prefix= True
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

# Start to find the images
img_dirs = []
img_dirs.append(dir_images)
if is_recursive:
    for subdir, dirs, files in os.walk(dir_images):
        for dir in dirs:
            img_dirs.append(os.path.join(subdir, dir))
for dir in img_dirs:
    lines = write_images(dir)