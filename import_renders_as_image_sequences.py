from pathlib import Path
import pymiere
from pymiere.wrappers import time_from_seconds
from array import array
import re

server_folder_name = "Renders"
prem_bin_name = "RENDERS"
potential_prem_bin_names = ["renders", "shotrenders", "mohorenders", "goeie renders"]

def main():
	print("---START---")
	if not is_premiere_ready():
		exit()
	project = pymiere.objects.app.project  # get premiere project
	renders_premiere_bin = find_or_create_renders_premiere_bin(project)
	imported_sequences = get_paths(renders_premiere_bin)
	renders_server_path = find_renders_server_folder(project)
	files_to_import = get_first_image_files(renders_server_path)
	files_to_import = remove(files_to_import, imported_sequences)
	import_as_image_sequences(project, renders_premiere_bin, files_to_import)
	rename_items(project)
	consolidate(project)
	print("---FINISHED---")

def find_renders_server_folder(project):
	print(f"Finding '{server_folder_name}' folder on server...")
	# Split the path into parts based on '/'
	prem_project_path = Path(project.path)
	prem_project_folder = prem_project_path.parent.parent
	print(f"FOLDER? {prem_project_folder}")
	# path_parts = prem_project_path.split('/')
	# Construct the new path by joining the necessary parts
	# path = '/'.join(path_parts[:-2]) + '/' + server_folder_name
	path = prem_project_folder.joinpath(server_folder_name)
	print(f"'{server_folder_name}' path: {path}")
	return path

def find_or_create_renders_premiere_bin(project):
	print(f"Finding '{prem_bin_name}' bin in Premiere project...")
	found_bin = False
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		for name in potential_prem_bin_names:
			lowercase = item.name.lower()
			if lowercase == name:
				item.renameBin(prem_bin_name)
		if item.name == prem_bin_name:
			found_bin = True
			return item
	if not found_bin:
		print(f"'{prem_bin_name}' not found, creating it.")
		project.rootItem.createBin(prem_bin_name)
		return find_or_create_renders_premiere_bin(project)

def get_paths(bin):
	print(f"Getting paths of items inside '{bin.name}'...")
	paths = []
	for i in range(bin.children.numItems):
		item = bin.children[i]
		path = item.getMediaPath()
		paths.append(path)
	return paths


def remove(files_to_import, imported_sequences):
	print("Removing already imported paths from list of files to import...")
	return [path for path in files_to_import if path not in imported_sequences]

def rename_items(project):
	print("Renaming...")
	episode_code = extract_prefix(project.name)
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == prem_bin_name:
			for j in range(item.children.numItems):
				child_item = item.children[j]
				name = child_item.name
				prefix = episode_code + "_"
				desired_name = remove_suffix(name)
				if desired_name.startswith(prefix):
					desired_name = desired_name[len(prefix):]
				if name != desired_name:
					child_item.name = desired_name
					print("Renamed: " + desired_name)

def extract_prefix(string):
	# Use regular expression to find the prefix
	match = re.match(r'^([A-Za-z]+[0-9]+)_', string)
	if match:
		return match.group(1)
	else:
		return None

def remove_suffix(name):
	# Regular expression to match the suffix pattern _00001 with any file extension
	match = re.search(r'_\d+\.\w+$', name)
	if match:
		return name[:match.start()]
	else:
		return name

def consolidate(project):
	print("Consolidating duplicates...")
	project.consolidateDuplicates()

def get_first_image_files(directory):
	print("Finding image sequence paths...")
	"""
	Get the first image file (alphabetically sorted) from each subdirectory and its subdirectories.
	
	Args:
	- directory: Path to the directory.
	
	Returns:
	- List of paths to the first image file from each subdirectory and its subdirectories.
	"""
	first_files = []
	root_path = Path(directory)
	
	for subfolder in root_path.rglob('*'):
		if subfolder.is_dir():
			# Gather all image files in the subdirectory
			image_files = sorted([f for f in subfolder.iterdir() if f.suffix.lower() in {'.png', '.jpg', '.jpeg'}])
			if image_files:
				first_files.append(str(image_files[0]))  # Get the first image file
	
	# Sort list alphabetically
	first_files.sort()
	return first_files

def is_premiere_ready():
	print("Finding Premiere...")
	# Print if premiere doc is opened
	is_ready = pymiere.objects.app.isDocumentOpen()
	if is_ready:
		print('Premiere project is open.')
	else:
		print('WARNING: No open Premiere project found!')
	return is_ready

def import_as_image_sequences(project, bin, file_paths):
	print(f"Importing {str(len(file_paths))} image sequences...")
	for file in file_paths:
		print("Importing " + file)
		this_file = []  # Array with a single file, because we want to import it as an image sequence.
		this_file.append(file)
		bin.select()
		project.importFiles(
			this_file,  # can import a list of media (Not if importAsNumberedStills == True!)
			suppressUI = True,
			targetBin = project.getInsertionBin(),
			importAsNumberedStills = True
		)

# Run main function
main()