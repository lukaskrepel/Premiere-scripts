import pymiere
from pymiere import wrappers
import random
import time

# Constants
ALLOWED_REPETITIVE_COUNT = 3
CLIP_FOLDER = "VOORCOMP_MP4"

# Define the weights for each category
CATEGORY_WEIGHTS = {
    'DinoFacts': 1,
    'Sketches': 0.6,
    'Construction': 0.5,
    'DinoDayCare': 0.4,
    'BabyMatch': 0.3,
    'Bones': 0.2,
    'ABC': 0.2
}
DEFAULT_WEIGHT = 0.1

# Main function to execute the script
def main():
    print("---START---")
    project = pymiere.objects.app.project
    # Get videos
    videos = get_videos(project)
    # Create a video playlist
    playlist = create_video_playlist(videos)
    # Generate project items list for the playlist
    arrayOfProjectItems = []
    for video in playlist:
        arrayOfProjectItems.append(video.projectItem)
    # Create a new sequence
    firstVideoCode = playlist[0].filename.split('_')[0]
    compilationCode = project.name.split('_')[0]
    sequence_name = compilationCode + "_Dinosaurs_Compilation_" + firstVideoCode
    project.createNewSequenceFromClips(sequence_name, arrayOfProjectItems)
    print("---FINISHED---")

# Video class to store video metadata
class Video:
    def __init__(self, filename, duration, category, projectItem):
        self.filename = filename
        self.duration = duration
        self.category = category
        self.projectItem = projectItem

    def __repr__(self):
        return f"{self.filename} ({time.strftime('%H:%M:%S', time.gmtime(self.duration))} min, {self.category})"

# Function to get all videos from the project
def get_videos(project):
    print("Getting videos...")
    videos = []
    for i in range(project.rootItem.children.numItems):
        item = project.rootItem.children[i]
        if item.name == CLIP_FOLDER:
            for j in range(item.children.numItems):
                childItem = item.children[j]
                category = childItem.name
                for k in range(childItem.children.numItems):
                    grandChildItem = childItem.children[k]
                    duration = (grandChildItem.getOutPoint(1).seconds - grandChildItem.getInPoint(1).seconds)
                    videos.append(Video(grandChildItem.name, duration, category, grandChildItem))
    return videos

# Function to create a video playlist with weighted random selection
def create_video_playlist(videos, target_duration=60*60):
    print("Creating playlist...")
    playlist = []
    total_duration = 0
    previous_category = None
    consecutive_sketches = 0

    while videos and total_duration < target_duration:
        # Filter valid videos based on the previous category and sketch constraints
        valid_videos = [
            video for video in videos
            if (video.category != previous_category or video.category == "Sketches")
        ]

        # Apply constraints for consecutive sketches
        if previous_category == "Sketches" and consecutive_sketches < 3:
            valid_videos = [video for video in valid_videos if video.category == "Sketches"]
        elif previous_category == "Sketches" and consecutive_sketches >= 3:
            valid_videos = [video for video in valid_videos if video.category != "Sketches"]

        if not valid_videos:
            break

        # Get the weights for the valid videos, using the default weight if the category is not defined
        weights = [CATEGORY_WEIGHTS.get(video.category, DEFAULT_WEIGHT) for video in valid_videos]
        next_video = random.choices(valid_videos, weights=weights, k=1)[0]
        
        playlist.append(next_video)
        videos.remove(next_video)
        total_duration += next_video.duration
        
        # Update the consecutive sketches counter
        if next_video.category == "Sketches":
            consecutive_sketches += 1
        else:
            consecutive_sketches = 0
        
        previous_category = next_video.category

    print("Total Duration: " + time.strftime('%H:%M:%S', time.gmtime(total_duration)))
    return playlist

# Run main function
main()
