from PIL import Image
import glob, os, sys, face_recognition, itertools, subprocess, concurrent.futures, numpy, pickle, datetime, time

is_verbose = ""


def collect_faces_of_dir(dir, verbose, collect, d_faces_unknown):
    global is_verbose
    is_verbose = verbose
    global is_collect
    is_collect = collect
    global dir_faces_unknown
    dir_faces_unknown = d_faces_unknown
    faces_of_dir = []
    images_to_read = []
    files_name_stored = []
    faces_of_dir_stored = read_db_faces_of_dir(dir)
    files = os.listdir(dir)
    for faces_of_image in faces_of_dir_stored:
        file_name_stored = faces_of_image[0]
        files_name_stored.append(file_name_stored)
        if file_name_stored in files:
            # yes, image exists
            faces_of_dir.append(faces_of_image)
    l = len(faces_of_dir)
    print("Read '"+ str(l) + "' image(s) from DB in directory " + dir)
    for filename in files:
        if filename in files_name_stored:
            continue
        file = os.path.join(dir, filename)
        if not os.path.exists(file):
            print_error("File does not exists. Excluded file from search for faces. " + file)
        if not is_image(file):
            if is_verbose: print("Skipping file because it is no image " + file)
            continue
        filesize = os.path.getsize(file)
        if not filesize > 0:
            if is_verbose: print("WARNING: Skipping file because file size is '0' " + file)
            continue

        details = []
        details.append(file)
        details.append(filename)
        images_to_read.append(details)
    l = len(images_to_read)
    print("Read '"+ str(l) + "' image(s) from files in directory " + dir)
    startTimeSeconds = time.time()
    storeDBafterSeconds = 60
    imageCounter = 0
    singleCPU = False
    if singleCPU:
        if is_verbose: print("Use one CPU only for dir " + dir)
        for details in images_to_read:
            imageCounter += 1
            if is_verbose: print(str(imageCounter) + " of " + str(l) + " is the next image...")
            result = collect_faces_image(details)
            lengthResult = len(result)
            if lengthResult > 0:
                faces_of_image = result[0]
                faces_of_dir.append(faces_of_image)
            faces_of_image = result[0]
            faces_of_dir.append(faces_of_image)
            currentSeconds = time.time()
            elapsed = currentSeconds - startTimeSeconds
            if elapsed > storeDBafterSeconds:            
                if is_verbose: print("About to store DB again after " + str(elapsed) + " seconds")
                #write_db_faces_of_dir(faces_of_dir, dir)
                startTimeSeconds = currentSeconds
    else:
        if is_verbose: print("Use all CPUs for dir " + dir)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Process the list of files, but split the work across the process pool to use all CPUs!
            for details, result in zip(images_to_read, executor.map(collect_faces_image, images_to_read)):
                l = len(result)
                if l > 0:
                    faces_of_image = result[0]
                    faces_of_dir.append(faces_of_image)
                currentSeconds = time.time()
                elapsed = currentSeconds - startTimeSeconds
                if elapsed > storeDBafterSeconds:            
                    if is_verbose: print("About to store DB again after " + str(elapsed) + " seconds")
                    #write_db_faces_of_dir(faces_of_dir, dir)
                    startTimeSeconds = currentSeconds
    write_db_faces_of_dir(faces_of_dir, dir)
    return faces_of_dir



def delete_temp_jpg(tmp_jpeg):
    if not tmp_jpeg == "":
        if is_verbose: print("Delete temp JPG " + tmp_jpeg)
        os.remove(tmp_jpeg)


def collect_faces_image(details):
    result = []
    file = details[0]
    img_orig, tmp_jpg = create_temp_jpg(file)
    if img_orig == "":
        if is_verbose: print("Ignored file. Is no image or creation of tmp JPG failed " + file)
        delete_temp_jpg(tmp_jpg)
        return result
    filename = details[1]
    file = img_orig
    if not tmp_jpg == "":
        file = tmp_jpg
    faces = []
    faces.append(filename)
    if is_verbose: print("Load face encodings from IMAGE... " + img_orig)
    # Load the jpg file into a numpy array
    if not os.path.exists(file):
        print_error("File does not exists. Can not load face encoding. " + file)
        delete_temp_jpg(tmp_jpg)
        return result
    try:
        image = face_recognition.load_image_file(file)
    except:
        if is_verbose: print("WARNING Skip this images. Why? Face_recognition failed to load file " + file)
        delete_temp_jpg(tmp_jpg)
        return result
    face_encodings = face_recognition.face_encodings(image)
    number_encodings = len(face_encodings)
    if is_verbose: print("Found '" + str(number_encodings) + "' faces in file " + img_orig)
    if number_encodings < 1:
        result.append(faces)
        delete_temp_jpg(tmp_jpg)
        return result
    face_locations = face_recognition.face_locations(image)
    number_locations = len(face_locations)
    if not number_locations == number_encodings:
        if is_verbose: print("WARNING found '" + str(number_encodings) + "' face encodings but '" + str(number_locations) + "' locations of faces in file " + img_orig)
        #result.append(faces)
        delete_temp_jpg(tmp_jpg)
        return result
    counter = 0
    for encoding in face_encodings:
        face = []
        location = face_locations[counter] # top, right, bottom, left
        face.append(encoding)
        face.append(location)
        counter += 1
        faces.append(face)
    result.append(faces)
    if is_collect:
        copy_faces_to_unkown(filename, image, face_locations, dir_faces_unknown)
    delete_temp_jpg(tmp_jpg)
    return result


def copy_faces_to_unkown(filename, image, face_locations, dir_faces_unknown):
    file, ext = os.path.splitext(filename)
    # Load the jpg file into a numpy array
    shape = image.shape
    image_hight = shape[0]
    image_width = shape[1]
    for face_location in face_locations:
        top, right, bottom, left = face_location
        # store the image file a little bit bigger
        # Why? sometimes the image is to small to regognize a face later on. Experimenting a bit helped but
        # not always.
        added_w = (bottom - top) // 10
        added_h = (right - left) // 10
        top_new = top - added_h
        if top_new < 1:
            top_new = 1
        bottom_new = bottom + added_h
        if bottom_new > image_hight:
            bottom_new = bottom
        left_new = left - added_w
        if left_new < 1:
            left_new = 1
        right_new = right + added_w
        if right_new > image_width:
            right_new = right
        # You can access the actual face itself like this:
        face_image = image[top_new:bottom_new, left_new:right_new]
        pil_image = Image.fromarray(face_image)
        #pil_image.show()
        img_name = "face-" + str(top_new) + "-" + str(left_new) + "-" + str(bottom_new) + "-" + str(right_new) + "_" + file + ".jpg"
        pil_image.save(dir_faces_unknown + "/" + img_name)
        print("Wrote face to '" + dir_faces_unknown + "/" + img_name)
    return


def read_known_faces(dir_faces_known, verbose):
    global is_verbose
    is_verbose = verbose
    faces_db, encodings_db = read_db(dir_faces_known)
    l = len(faces_db)
    if is_verbose: print("Read '" + str(l) + "' face encodings from DB")
    know_faces_files = []
    for subdir, dirs, files in os.walk(dir_faces_known):
        for file in files:
            known_img = os.path.join(subdir, file)
            # check if image is already encoded
            found = False
            for face in faces_db:
                path = face[0]
                if path == known_img:
                    # was encoded already
                    found = True
                    break
            if not found:
                know_faces_files.append(known_img)
    # remove encodings without image
    faces = []
    encodings = []
    counter = 0
    for face in faces_db:
        path = face[0]
        if os.path.exists(path):
            faces.append(face)
            encodings.append(encodings_db[counter])
        else:
            if is_verbose: print("Removed face enconding from DB " + path)
        counter += 1
    l = len(know_faces_files)
    if is_verbose: print("Read '" + str(l) + "' face encodings from images")
    # create directory for defect faces (images containing not exactly on face)
    dir_faces = os.path.abspath(os.path.join(dir_faces_known, os.pardir))
    global dir_defect
    dir_defect = os.path.join(dir_faces, "defect")
    if not os.path.exists(dir_defect):
        os.mkdir(dir_defect)
    with concurrent.futures.ProcessPoolExecutor() as executor:
    # Process the list of files, but split the work across the process pool to use all CPUs!
        for file, face_details in zip(know_faces_files, executor.map(read_known_face, know_faces_files)):
            #if is_verbose : print("Finished reading known face from file " + file)
            if len(face_details) == 3:
                faces.append(face_details)
                face_encoding = face_details[2]
                encodings.append(face_encoding)
    write_db(faces, encodings, dir_faces_known)
    return faces, encodings


def read_known_face(known_img):
    "Read in the encodings of known faces"
    face_details = []
    subdir = os.path.dirname(known_img)
    face_name = os.path.basename(subdir)
    if is_verbose: print("Load face encoding from IMAGE... " + known_img)
    # Load the jpg file into a numpy array
    image = face_recognition.load_image_file(known_img)
    numberofelements = len(face_recognition.face_encodings(image))
    if not numberofelements == 1:
        mv_file_name = os.path.basename(known_img)
        movedfile = os.path.join(dir_defect, mv_file_name)
        os.rename(known_img, movedfile)
        if is_verbose: print(
        "WARNING: Found '" + str(numberofelements) + "' faces in file. Expected exactly  '1'. Moved to " + movedfile)
        return face_details
    face_encoding = face_recognition.face_encodings(image)[0]
    face_details.append(known_img)
    face_details.append(face_name)
    face_details.append(face_encoding)
    return face_details;


def compare_face(unknown_face_encoding, known_faces, known_encodings, face_tolerance, verbose):
    global is_verbose
    is_verbose = verbose
    nearest_face = ""
    nearest_encoding = 1.0
    results = face_recognition.compare_faces(known_encodings, unknown_face_encoding, face_tolerance)
    face_distances = face_recognition.face_distance(known_encodings, unknown_face_encoding)
    counter = 0
    for result in results:
        if result:
            face_name = known_faces[counter] [1]
            distance = face_distances[counter]
            #print(str(result) + " > " + face_name + str(distance))
            if distance < nearest_encoding:
                nearest_encoding = distance
                nearest_face = face_name
        counter = counter + 1
    return nearest_face, nearest_encoding


def create_temp_jpg(file):
    "Check if image file and create a temporary JPG for RAW file"
    tmp_jpg = ""
    extentions = ['jpg', 'bmp', 'png', 'gif']
    for ext in extentions:
        if file.lower().endswith(ext):
            return file, tmp_jpg
    extentions_raw = ['cr2', 'dng']
    for ext in extentions_raw:
        if file.lower().endswith(ext):
            if is_verbose: print("Convert RAW > JPG " + file)
            return_code = subprocess.call(["ufraw-batch", "--silent", "--out-type", "jpg", file])
            base = os.path.basename(file)
            filename, ext = os.path.splitext(base)
            dirname = os.path.dirname(file)
            tmp_jpg = os.path.join(dirname, filename + ".jpg")
            if not os.path.exists(tmp_jpg):
                print_error("Failed to create temp JPG from RAW file. Temp JPG should be " + tmp_jpg)
                return "", ""
            else:
                return file, tmp_jpg
    return "", "";


def is_image(file):
    extentions = ['jpg', 'bmp', 'png', 'gif', 'cr2', 'dng']
    for ext in extentions:
        if file.lower().endswith(ext):
            return True
    return False


def filter_images(files, extentions):
    "Check return all image files as list"
    images = []
    for file in files:
        for ext in extentions:
            if file.lower().endswith(ext):
                images.append(file)
    all = len(files)
    fil = len(images)
    if is_verbose: print("'" + str(fil) + "' out of " + str(all) + "' files are images.")
    return images;


def write_db(faces, encodings, dir_faces_known):
    db = []
    db.append(faces)
    db.append(encodings)
    dir_faces = os.path.abspath(os.path.join(dir_faces_known, os.pardir))
    db_file = os.path.join(dir_faces, "faces.db")
    output = open(db_file, 'wb')
    pickle.dump(db, output, pickle.HIGHEST_PROTOCOL)
    output.close()


def read_db(dir_faces_known):
    dir_faces = os.path.abspath(os.path.join(dir_faces_known, os.pardir))
    db_file = os.path.join(dir_faces, "faces.db")
    faces = []
    encodings = []
    if os.path.exists(db_file):
        input = open(db_file, 'rb')
        db = pickle.load(input)
        input.close()
        l = len(db)
        if l == 2:
            faces = db[0]
            encodings = db[1]
    return faces, encodings


def write_db_faces_of_dir(faces_of_dir, dir):
    db_file = os.path.join(dir, ".faces_of_dir.db")
    output = open(db_file, 'wb')
    pickle.dump(faces_of_dir, output, pickle.HIGHEST_PROTOCOL)
    output.close()
    if is_verbose: print("Wrote DB " + dir + ".faces_of_dir.db")


def read_db_faces_of_dir(dir):
    db_file = os.path.join(dir, ".faces_of_dir.db")
    faces_of_dir = []
    if os.path.exists(db_file):
        input = open(db_file, 'rb')
        faces_of_dir = pickle.load(input)
        input.close()
    return faces_of_dir


def read_faces_csv_line(line):
    # Example line
    #  '/home/vm/Dokumente/import-faces/images/800px-Obama_family_portrait_in_the_Green_Room.jpg;2017-11-11 16:48:16.862618;129 315 191 377 0.53 Michelle Obama;156 487 218 550 0.13 Michelle'
    parts = line.split(";")
    if len(parts) < 3:
        return "" # ignore, format not ok
    line_details = []
    line_details.append(parts[0]) # path
    line_details.append(parts[1]) # timestamp
    boxes = []
    i = 0
    for person in parts:
        if i > 1:
            box = []
            details = person.split(" ")
            if len(details) < 6:
                continue # ignore, format not ok
            top = details[0]
            left = details[1]
            height = details[2]
            width = details[3]
            similarity = details[4]
            name = ""
            j = 0
            for name_part in details:
                # in case the name has blanks like 'Barack Obama'
                if j > 4:
                    if not name == "":
                        name += " "
                    name += name_part
                j += 1
            box.append(name)
            box.append(top)
            box.append(left)
            box.append(height)
            box.append(width)
            box.append(similarity)
            boxes.append(box)
        i += 1
    line_details.append(boxes)
    return line_details


def print_error(message):
    time_string = datetime.datetime.now()
    msg = str(time_string) + " " + message + "\n"
    if is_verbose: print(msg)
    open("error.log", "a").write(msg)
