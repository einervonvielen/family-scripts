from PIL import Image
import glob, os, sys, itertools, subprocess, concurrent.futures, face_util, shutil, PIL

global dir_images
global dir_faces
global dir_exclude_arg
global face_tolerance
global is_verbose
global is_exiftool


def print_help():
    print(" ")
    print("Find person in files and copy images to a directory 'found'")
    print(" ")
    print("Steps")
    print("1. Read the hidden file '.faces.csv' in a (sub)directory")
    print("2. Find the person in '.faces.csv' and copy the image")
    print("   containing the person into a directory './found/person/'")
    print("   Convert RAW images to JPEG if neccessary)")
    print("3. (optional param '-html')")
    print("   - html")
    print(" ")
    print("Usage: ")
    print(" ")
    print("python3 find.py -p person -i image-dir [ -r ] [ -html ] [ -v ] [ -h ]")
    print("  -p person")
    print("    AND search:")
    print("      If you want to find images with 'Bob' AND 'Jane' use")
    print("      '-p Bob -p Jane")
    print("      '-p Bob -p Jane")
    print("    Blank spaces in name:")
    print("      If names contain a blank space 'Barack Obama' use quotation marks")
    print("      -p \"Barack Obama\"")
    print("  -i image-dir")
    print("    Where to find the image file.")
    print("  -r")
    print("    recursive -  traverse subdirectories of image-dir recursively.")
    print("  -html")
    print("    write HTML file showing faces framed and named")
    print("  -v")
    print("    verbose. Prints more messages.")
    print("  -h or --help")
    print("    Print this help message.")
    quit()


def write_images(dir, html_parts):
    csv_file = os.path.join(dir, ".faces.csv")
    if not os.path.exists(csv_file):
        return
    input = open(csv_file, 'r')
    lines = input.read().splitlines()
    input.close()
    for line in lines:
        img_details = find(line, dir)
        if not len(img_details) < 1:
            html_parts.append(img_details)
        else:
            if is_verbose: print("Person not found in dir " + dir)
    return html_parts


def find(line, dir):
    if is_verbose: print("Read CSV line " + line)
    details = face_util.read_faces_csv_line(line)
    if len(details) < 1:
        return ""
    path = details[0]
    path = os.path.join(dir, path)
    if not os.path.exists(path):
        return ""
    boxes = details[2]
    # copy files
    img_details = []
    find_counter = 0
    check_double = ""
    for face_name in face_names:
        for box in boxes:
            person = box[0]
            if person == face_name:
                if not person in check_double:
                    find_counter += 1
                    check_double += person
    if find_counter == len(face_names):
        file_name = os.path.basename(path)
        # copy image
        dst = os.path.join(dir_face_name, file_name)
        shutil.copyfile(path, dst)
        print(dst)
        # write html file with framed and named faces
        if is_html:
            # create temp JPG if image is RAW
            img_orig, tmp_jpg = face_util.create_temp_jpg(dst);
            if not tmp_jpg == "":
                dst = tmp_jpg
            # a html file with named frames around a face
            img_details = create_html_for_image(dst, boxes)
            img_details.append(dir_face_name)
            if not tmp_jpg == "":
                # Remove RAW image
                os.remove(img_orig)
    return img_details


def create_html_for_image(img, boxes):
    file_name = os.path.basename(img)
    thumbnail_param_names = ""
    thumbnail_param_left = ""
    thumbnail_param_top = ""
    thumbnail_param_width = ""
    thumbnail_param_font_size = ""
    html_boxes = ""
    for box in boxes:
        # top = box[1], right = box[2], bottom = box[3], left = box[4]
        name, face_top, face_left, face_height, face_width, similarity = box
        if not thumbnail_param_names == "":
            thumbnail_param_names += "/"
        thumbnail_param_names += name
        if not thumbnail_param_left == "":
            thumbnail_param_left += "/"
        thumbnail_param_left += face_left
        if not thumbnail_param_top == "":
            thumbnail_param_top += "/"
        thumbnail_param_top += face_top
        font_size = str(round(int(face_width) / 7))
        if not thumbnail_param_font_size == "":
            thumbnail_param_font_size += "/"
        thumbnail_param_font_size += font_size
        if not thumbnail_param_width == "":
            thumbnail_param_width += "/"
        thumbnail_param_width +=  face_width
        box_style = "top: calc(" + face_top + "px + 15vw); left: " + face_left + "px; width: " + face_width + "px; height: " + face_height + "px; font-size: " + font_size + "px;"
        html_boxes += "      <!-- similarity " + similarity + "-->\n"
        html_boxes += "      <div id=\"box\" style=\"" + box_style + "\">" + name + "</div>\n"
    thumbnail_params = "'" + file_name + "', '" + thumbnail_param_names + "', '" + thumbnail_param_top + "', '" + thumbnail_param_left + "', '" + thumbnail_param_width + "', '" + thumbnail_param_font_size + "'"
    img_details = []
    img_details.append(file_name)
    img_details.append(thumbnail_params)
    img_details.append(html_boxes)
    return img_details


def write_face_to_html(html_parts):
    html = ""
    html += "<html>\n"
    html += "<script>\n"
    html += "function show_picture(img, names, tops, lefts, widths, font_sizes) {\n"
    html += "   var picture = document.getElementById(\"picture\");\n"
    html += "   picture.src = img;\n"
    html += "   var a_names = names.split('/');\n"
    html += "   var a_tops = tops.split('/');\n"
    html += "   var a_lefts = lefts.split('/');\n"
    html += "   var a_widths = widths.split('/');\n"
    html += "   var a_font_sizes = font_sizes.split('/');\n"
    html += "   var l = a_names.length;\n"
    html += "   var boxes = \"\";\n"
    html += "   for (var i = 0; i < l; i++) {\n"
    html += "       box_style = \"top: calc(\" + a_tops[i] + \"px + 15vw); left: \" + a_lefts[i] + \"px; width: \" + a_widths[i] + \"px; height: \" + a_widths[i] + \"px; font-size: \" + a_font_sizes[i] + \"px;\"\n"
    html += "       boxes += \"<div id='box' style='\" + box_style + \"'>\" + a_names[i] + \"</div>\"\n"
    html += "   }\n"
    html += "   var box = document.getElementById(\"boxes\");\n"
    html += "   box.innerHTML = boxes;\n"
    html += "}\n"
    html += "</script>\n"
    html += "<noscript> No Java Script activated. </noscript>\n"
    html += "<style>\n"
    html += "#preview {\n"
    html += "  height: 15vw;\n"
    html += "  overflow-x: auto;\n"
    html += "  white-space: nowrap;\n"
    html += "}\n"
    html += "#thumbnail {\n"
    html += "  height: 12vw;\n"
    html += "}\n"
    html += "#box {\n"
    html += "  position: absolute;\n"
    html += "  border: 3px dashed  #F00;\n"
    html += "  text-align: center; color: #F00;\n"
    html += "}\n"
    html += "</style>\n"
    html += " <body>\n"
    html += "    <div id=\"preview\">\n"
    for img_details in html_parts:
        file_name, thumbnail_params, html_boxes, dir = img_details
        html += "    <img id=\"thumbnail\" src=\"" + file_name + "\" onclick=\"show_picture(" + thumbnail_params + ")\">\n"
    html += "    </div>\n"
    for img_details in html_parts:
        file_name, thumbnail_params, html_boxes, dir = img_details
        html += "    <img id=\"picture\" src=\"" + file_name + "\">\n"
        html += "    <div id=\"boxes\">\n"
        html += html_boxes
        break
    html += "    </div>\n"
    html += "</body>\n"
    html += "</html>\n"
    path = os.path.join(dir, "index.html")
    html_file = open(path, 'w')
    try:
        html_file.write(html)
    finally:
        html_file.close()
    print(path)
    return


dir_images_arg = ""
dir_images = ""
face_names = []
next_arg = ""
is_recursive = False
is_verbose = False
is_html = False
for arg in sys.argv[1:]:
    assert isinstance(arg, object)
    if arg == '-i':
        next_arg = "-i"
    elif next_arg == '-i':
        dir_images_arg = arg
        next_arg = ""
    elif arg == '-p':
        next_arg = "-p"
    elif next_arg == '-p':
        face_names.append(arg)
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

if len(face_names) < 1:
    print("No name of person given. Use parameter '-p name'.")
    print_help()

dir_found = os.path.join(dir_script, "found")
if not os.path.exists(dir_found):
    os.mkdir(dir_found)

dir_name = ""
for face_name in face_names:
    if not dir_name == "":
        dir_name += " AND "
    dir_name += face_name
dir_face_name = os.path.join(dir_found, dir_name)
if not os.path.exists(dir_face_name):
    os.mkdir(dir_face_name)

# Start to find the images
img_dirs = []
img_dirs.append(dir_images)
if is_recursive:
    for subdir, dirs, files in os.walk(dir_images):
        for dir in dirs:
            img_dirs.append(os.path.join(subdir, dir))
html_parts = []
for dir in img_dirs:
    html_parts = write_images(dir, html_parts)

if len(html_parts) < 1:
    if is_verbose: print("Person(s) not found in dir")
else:
    if is_html:
        write_face_to_html(html_parts)