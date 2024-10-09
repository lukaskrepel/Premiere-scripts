import LK_pymiere

def main():
	print("---START---")
	if not LK_pymiere.is_premiere_ready():
		exit()
	project = LK_pymiere.get_project()
	LK_pymiere.consolidate_duplicates(project)
	LK_pymiere.consolidate_audio_bins(project)
	LK_pymiere.remove_unused(project)
	print("---FINISHED---")

# Run main function
main()