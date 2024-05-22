import pymiere
from pymiere import wrappers
import random
import time

ALLOWED_REPETITIVE_COUNT = 3
CLIP_FOLDER = "VOORCOMP_MP4"


# Main function to execute the script
def main():
	print("---START---")
	# Get videos
	videos = get_videos()
	playlist = create_video_playlist(videos)
	# Print de gegenereerde afspeellijst
	arrayOfProjectItems = []
	for video in playlist:
		print(video)
		arrayOfProjectItems.append(video.projectItem)
	# Create a new sequence
	project = pymiere.objects.app.project
	sequence_name = "CP00_Dinosaurs_Compilation_XX"
	project.createNewSequenceFromClips(sequence_name, arrayOfProjectItems)
	print("---FINISHED---")


class Video:
	def __init__(self, filename, duration, category, projectItem):
		self.filename = filename
		self.duration = duration
		self.category = category
		self.projectItem = projectItem

	def __repr__(self):
		return f"{self.filename} ({time.strftime('%H:%M:%S', time.gmtime(self.duration))} min, {self.category})"


def get_videos():
	print("Getting videos...")
	videos = []
	project = pymiere.objects.app.project
	for i in range (0, project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == CLIP_FOLDER:
			for j in range (0, item.children.numItems):
				childItem = item.children[j]
				category = childItem.name
				#print("Category: " + category)
				for k in range (0, childItem.children.numItems):
					grandChildItem = childItem.children[k]
					#print("Video: " + grandChildItem.name)
					duration = (grandChildItem.getOutPoint(1).seconds - grandChildItem.getInPoint(1).seconds)
					videos.append(Video(grandChildItem.name, duration, category, grandChildItem)) # This is how we'll add videos #TODO add item(?)
	return videos


def create_video_playlist(videos, target_duration=60*60):
	print("Creating playlist...")
	playlist = []
	total_duration = 0
	previous_category = None
	consecutive_sketches = 0

	while videos and total_duration < target_duration:
		valid_videos = [
			video for video in videos
			if (video.category != previous_category or video.category == "Sketches")
		]

		if previous_category == "Sketches" and consecutive_sketches >= 3:
			valid_videos = [
				video for video in valid_videos
				if video.category != "Sketches"
			]

		if not valid_videos:
			break

		next_video = random.choice(valid_videos)
		playlist.append(next_video)
		videos.remove(next_video)
		total_duration += next_video.duration
		
		if next_video.category == "Sketches":
			consecutive_sketches += 1
		else:
			consecutive_sketches = 0
		
		previous_category = next_video.category
	print("Total Duration: " + time.strftime('%H:%M:%S', time.gmtime(total_duration)))
	return playlist


# Run main function
main()