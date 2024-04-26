# Premiere scripts
Scripts for Adobe Premiere, to be used with pymiere.
## How to
Make sure you install pymiere first by running this command in the Terminal:
```
python -m pip install pymiere
```
Then, while having your Adobe Premiere project opened, run:
```
python /location_of_the_script/import_renders_as_image_sequences.py
```
## Suggested folder structure for projects
> [!IMPORTANT]
> Your Premiere project needs to be in the Edit folder.
> Running `import_renders_as_image_sequences.py` will:
> - Import all image sequences from each subfolder of the `Renders` folder into a `RENDERS` bin in your Premiere project.
> - It will rename the item in Premiere from 'EP01_001_Intro_00001.jpg' to '001_Intro'.
> - It wil consolidate duplicate items in Premiere (so you can run it multiple times, for example, after new shots have been rendered).
- EP01_Pilot
  - Edit
    - EP01_Pilot_v001_L.prproj
  - Renders
    - EP01_001_Intro
      - EP01_001_Intro_00001.jpg
      - EP01_001_Intro_00002.jpg
      - EP01_001_Intro_00003.jpg
    - EP01_002_SomethingHappens
      - EP01_002_SomethingHappens_00001.jpg
      - EP01_002_SomethingHappens_00002.jpg
      - EP01_002_SomethingHappens_00003.jpg
    - EP01_003_Etcetera
      - EP01_003_Etcetera_00001.jpg
      - EP01_003_Etcetera_00002.jpg
      - EP01_003_Etcetera_00003.jpg
