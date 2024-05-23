import pathlib
import pymiere
from pymiere.wrappers import time_from_seconds
from array import array

server_folder_name = "Renders"
prem_bin_name = "RENDERS"
potential_prem_bin_names = ["renders", "shotrenders", "mohorenders"]

def main():
	print("---START---")
	if not is_premiere_ready():
		exit()
	project = pymiere.objects.app.project  # get premiere project
	renders_premiere_bin = find_or_create_renders_premiere_bin(project)
	imported_sequences = get_paths(renders_premiere_bin)
	renders_server_path = find_renders_server_folder(project)
	files_to_import = get_first_files(renders_server_path)
	files_to_import = remove(files_to_import, imported_sequences)
	import_as_image_sequences(project, renders_premiere_bin, files_to_import)
	rename_items(project)
	consolidate(project)
	print("---FINISHED---")

def find_renders_server_folder(project):
	print("Finding '" + server_folder_name + "' folder on server...")
	# Split the path into parts based on '/'
	path_parts = project.path.split('/')
	# Construct the new path by joining the necessary parts
	path = '/'.join(path_parts[:-2]) + '/' + server_folder_name
	print("'" + server_folder_name + "' path: " + path)
	return path

def find_or_create_renders_premiere_bin(project):
	print("Finding '" + prem_bin_name + "' bin...")
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
		project.rootItem.createBin(prem_bin_name)
		return find_or_create_renders_premiere_bin(project)

def get_paths(bin):
	print("Getting paths of items inside '" + bin.name + "'...")
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
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == prem_bin_name:
			for j in range(item.children.numItems):
				child_item = item.children[j]
				name = child_item.name
				first_underscore_index = name.find('_')  # Find the index of the first underscore
				last_underscore_index = name.rfind('_')  # Find the index of the last underscore
				if first_underscore_index < last_underscore_index:
					desired_name = name[first_underscore_index + 1:last_underscore_index]  # Extract the desired substring
					child_item.name = desired_name
					print("Renamed: " + desired_name)

def consolidate(project):
	print("Consolidating duplicates...")
	project.consolidateDuplicates()

def get_first_files(directory):
	print("Finding image sequence paths...")
	"""
	Get the first file (alphabetically sorted) from each subdirectory.
	
	Args:
	- directory: Path to the directory.
	
	Returns:
	- List of paths to the first file from each subdirectory.
	"""
	first_files = []
	path = pathlib.Path(directory)
	for item in path.iterdir():
		if item.is_dir():
			sub_files = list(item.glob('*'))
			if sub_files:
				first_files.append(str(min(sub_files)))
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
	print("Importing " + str(len(file_paths)) + " image sequences...")
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