import csv

import pymiere
from pymiere import wrappers
import time
import re
import platform

import LK_pymiere

# IMPORTANT!
# Premiere files should use this filename convention:
# "CP001_DinosaursHalloween_ABC01_v001_L.prproj"
# (compilation_code / tags_capilatized / first_episode_code / file_version / author_initial / extension)

# Constants
CLIP_FOLDER_NAME = "VOORCOMP_MP4"

ROW = 2

# Main function to execute the script
def main():
    print("---START---")
    if not LK_pymiere.is_premiere_ready():
        exit()
    project = LK_pymiere.get_project() # project = pymiere.objects.app.project
    qe_project = pymiere.objects.qe.project
    # Split by underscore (_) and extract the relevant part

    write_to_csv("codename", "category", "filename", "inpoint", "outpoint", "duration", "tags", "age_range", "rating", "short_description", "long_description")

    get_videos(project)
    print("---FINISHED---")

# Function to get all videos from the project
def get_videos(project):
    row = 2
    print("Getting videos...")
    videos = []
    for i in range(project.rootItem.children.numItems):
        item = project.rootItem.children[i]
        if item.name == CLIP_FOLDER_NAME:
            for j in range(item.children.numItems):
                childItem = item.children[j]
                category = childItem.name
                print("- Category: " + category)
                for k in range(childItem.children.numItems):
                    grandChildItem = childItem.children[k]
                    # CHECK DESCRIPTION:
                    metadata = grandChildItem.getProjectMetadata()
                    # Regular expression to capture the comment part
                    comment = re.search(r'<premierePrivateProjectMetaData:Column\.PropertyText\.Comment>(.*?)</premierePrivateProjectMetaData:Column\.PropertyText\.Comment>', metadata)
                    tags = ""
                    if comment:
                        tags = comment.group(1)
                    #
                    codename = grandChildItem.name
                    mediapath = grandChildItem.getMediaPath()
                    filename = mediapath.split("\\")[-1]
                    inpoint = grandChildItem.getInPoint(1).seconds
                    outpoint = grandChildItem.getOutPoint(1).seconds
                    rounded_inpoint = round(inpoint, 2)
                    rounded_outpoint = round(outpoint, 2)
                    duration = rounded_outpoint - rounded_inpoint
                    rounded_duration = round(duration, 2)
                    print(rounded_duration)
                    age_range = '1-3'
                    if category == 'DinoRangers' or category == 'DinoFacts':
                        age_range = '3-5'
                    elif category == 'Sketches':
                        age_range = '1-5'
                    rating = ''
                    description = ''
                    category = mediapath.split("\\")[-2]
                    write_to_csv(codename, category, filename, rounded_inpoint, rounded_outpoint, rounded_duration, tags, age_range, rating, description)
                    row += 1

def write_to_csv(codename='', category='', filename='', inpoint='', outpoint='', duration='', tags='', age_range='', rating='', short_description='', long_description=''):
    write_csv_row([codename, category, filename, inpoint, outpoint, duration, tags, age_range, rating, short_description, long_description])

def write_csv_row(values):
    print(f"Writing to CSV row: {values}.")
    # Open the CSV file in append mode
    with open('voorcomp_data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the value to the specified cell
        writer.writerow(values)

# Run main function
main()
