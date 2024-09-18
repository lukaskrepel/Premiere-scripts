import pymiere

# Main function
def main():
	app = pymiere.objects.app
	scratchDiskTypes = { ScratchDiskType.FirstVideoPreviewFolder, ScratchDiskType.FirstAudioPreviewFolder}
	for scratchDiskType in scratchDiskTypes:
		app.setScratchDiskPath("/Users/lukas/Scratch Disks Premiere/", scratchDiskType)

# Run main function
main()