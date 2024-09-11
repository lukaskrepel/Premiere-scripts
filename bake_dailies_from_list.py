import pymiere
from pymiere import wrappers
import re
import os
import pymiere.exe_utils as pymiere_exe
import requests
import bake_daily # bake_daily.py in same folder?

# Constants
# list of project paths to bake dailies of, currently better just stick to 1 single project.
PROJECT_PATHS = {
	"/Volumes/megagamma_data/Club Baboo/SHOTS/DinoFacts/DF09_Parasaurolophus"
}

def main():
	print("---START---")
	for project_path in PROJECT_PATHS:
		edit_path = latest_edit_file(project_path)
		print(edit_path)
		if not os.path.isfile(edit_path):
			print("Example prproj path does not exists on disk '{}'".format(EXAMPLE_PRPROJ))
		# start premiere
		print("Starting Premiere Pro...")
		if pymiere_exe.is_premiere_running()[0]:
			print("There already is a running instance of premiere")
		pymiere_exe.start_premiere()
		#
		# open a project
		print("Opening project '{}'".format(edit_path))
		error = None
		# here we have to try multiple times, as on slower systems there is a slight delay between Premiere initialization
		# and when the PymiereLink panel is started and ready to receive commands. Most install will succeed on the first loop
		for x in range(20):
			try:
				pymiere.objects.app.openDocument(edit_path)
			except Exception as error:
				time.sleep(0.5)
			else:
				break
		else:
			print("Couldn't open path '{}'".format(edit_path))
		bake_daily.main()
		# close?
		print("---FINISHED---")


def latest_edit_file(project_path):
	project_path = project_path + "/Edit/"
	# Regular expression to match version numbers in the filenames
	version_pattern = re.compile(r'_v(\d{3})_[A-Za-z]+\.prproj')
	# List to store matched files with version numbers
	files_with_versions = []
	# Loop through the files in the directory
	for file_name in os.listdir(project_path):
		match = version_pattern.search(file_name)
		if match:
			version_number = int(match.group(1))  # Extract version number
			files_with_versions.append((version_number, file_name))
	# If there are any matching files, pick the one with the highest version number
	if files_with_versions:
		latest_file = max(files_with_versions, key=lambda x: x[0])[1]
		print(f"The latest version file is: {latest_file}")
	else:
		print("No matching files found.")
	return project_path + latest_file

# Run main function
main()