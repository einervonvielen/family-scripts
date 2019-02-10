import glob, os, sys, subprocess


def print_help():
	print("Create a photo diary from EXIF data.")
	print(" ")
	print("Usage: ")
	print(" ")
	print("python3 diary.py -i image-dir -v -h")
	print("  -i image-dir")
	print("    Where to find the image file.")
	print("  -v")
	print("    verbose. Prints more messages.")
	print("  -h or --help")
	print("    Print this help message.")
	quit()


def is_image(file):
    extentions = ['jpg', 'bmp', 'png', 'gif', 'cr2', 'dng']
    for ext in extentions:
        if file.lower().endswith(ext):
            return True
    return False


dir_images_arg = ""
dir_images = ""
is_verbose = False
next_arg = ""
for arg in sys.argv[1:]:
	assert isinstance(arg, object)
	if arg == '-i':
		next_arg = "-i"
	elif next_arg == '-i':
		dir_images_arg = arg
		next_arg = ""
	elif arg == '-v':
		is_verbose = True
	elif arg == '-h' or arg == '--help':
		print_help()

dir_script = os.path.dirname(os.path.realpath(__file__))
if is_verbose: print("Dir of script is " + dir_script)

# Check directory for images
if dir_images_arg == "":
	dir_images = "./"
	if is_verbose: print("Parameter -i not given. Search the images in " + dir_images)
else:
	if not os.path.exists(dir_images_arg):
		sys.exit("Directory for images not existing. Dir =  " + dir_images_arg)
	dir_images = dir_images_arg;


# Start to find the images
files = os.listdir(dir_images)
html = "<html>\n"
html += "<head>\n"
html += "<meta charset='utf-8'/>\n"
html += "<style>\n"
html += "img { width: 90%; }\n"
html += "div.title { color: green; }\n"
html += "div.description { color: black; }\n"
html += "</style>\n"
html += "</head>\n"
html += "<body>\n"
html += "</body>\n"
html += "</html>\n"
for img in files:
	if os.path.isdir(img): continue
	if is_image(img):
		img_path = dir_images + "/" + img
		html += "<p>\n"
		if is_verbose: print("image: " + img)
		html_img = "<img src='" + img_path + "'>\n"
		html_title = ""
		html_description = ""
		exiftool_out = subprocess.run(["exiftool", img_path], stdout=subprocess.PIPE)
		exiftool_out = exiftool_out.stdout.decode('utf-8')
		exif_array = exiftool_out.split("\n")
		for exif_data in exif_array:
			key_value = exif_data.split(":", 1)
			key = key_value[0].lower().strip()
			if(key == "title" or key == "xp title"):
				if is_verbose: print("Title:" + key_value[1])
				html_title = "<div class=\"title\">" + key_value[1] + "<div> \n"
			if(key == "image description"):
				if is_verbose: print("description:" + key_value[1])
				html_description = "<div class=\"description\">" + key_value[1] + "<div> \n"
		html += html_title
		html += html_img
		html += html_description
		html += "</p>\n"
	else:
		if is_verbose: print("is no *.jpg: " + img)

open("diary.html", "w+").write(html)

quit()



