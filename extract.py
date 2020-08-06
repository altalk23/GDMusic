import os
import sys
import requests
import time
import re
from shutil import copy
from datetime import datetime
from eyed3 import id3
import eyed3
from html2text import html2text
from progress.bar import Bar

# Get the current working directory
cwdir = os.getcwd()

# Get the home directory
homedir = os.path.expanduser("~")

# Create the music directory if not exists
musicdir = os.path.join(cwdir, "music")
if not os.path.exists(musicdir):
    os.mkdir(musicdir)

# Get the cache directory
if sys.platform == "darwin":
    cachedir = os.path.join(homedir, "Library", "Caches")
else:
    raise NotImplementedError

# Get the list of all music ids
idlist = [f[:-4] for f in os.listdir(cachedir) if f[-4:] == ".mp3"]

# Create a progress bar
bar = Bar('Extracting', fill='█', max=len(idlist))

# Disable warnings
eyed3.log.setLevel("ERROR")

# Get the list of all previous music ids
musiclist = [re.findall("\\[\\d+\\]", f)[0][1:-1] for f in os.listdir(musicdir) if f[-4:] == ".mp3"]

# Do for each id
for id in idlist:

    # Check if already exists
    if id not in musiclist:

        # Set the url for requesting
        ngurl = f"url=newgrounds.com/audio/listen/{id}"
        apiurl = f"https://api.newgrounds.app/details.php?{ngurl}"
        
        try:
            # Request the content
            content = requests.get(apiurl).json()
            
            # Get metadata
            title = content["audio_details"][0]["name"]
            artist = content["audio_details"][0]["artist"]
            comment = html2text(content["description"][0]["details"])
            genre = content["information"][0]["genre"]
            releasedate = content["information"][0]["uploaded"]
            imageurl = content["audio_details"][0]["icon"]
            
            contact = True
            
        except:
            # The music is deleted or removed
            contact = False
           
            # Get file locations
            cachefile = os.path.join(cachedir, f"{id}.mp3")
            musicfile = os.path.join(musicdir, f"Unknown [{id}].mp3")

            # Copy the music file to the directory
            copy(cachefile, musicfile)
            
        if contact:
        
            # Remove special characters from title
            title = re.sub('[<>:"/\\|?*]', "", title)
                
            # Get year from unix timestamp
            uploadtime = datetime.fromtimestamp(releasedate)
            year = eyed3.core.Date(uploadtime.year)
            
            # Get file locations
            cachefile = os.path.join(cachedir, f"{id}.mp3")
            musicfile = os.path.join(musicdir, f"{title} [{id}].mp3")
            
            # Copy the music file to the directory
            copy(cachefile, musicfile)
            
            # Create mp3 tag
            tag = id3.tag.Tag()
            tag.parse(musicfile)
            tag.header.version = id3.ID3_V2_3
            
            # Set tag values
            tag.artist = artist
            tag.title = title
            tag.album = f"{title} [{id}]"
            tag.genre = genre
            tag.recording_date = year
            tag.comments.set(comment)
            
            try:
                # Get image data
                response = requests.get(imageurl)
                imagedata = response.content
                
                # Set image data
                tag.images.set(type_=3, img_data=imagedata, mime_type="image/png")
                
            except:
                pass

            # Save the tag
            tag.save(encoding="utf-8")
        
    bar.next()
    
print(f"\nFinished, saved to {musicdir}")
