import os
import sys
import requests
import time
import re
import pickle
from shutil import copy
from datetime import datetime
from eyed3 import id3
import eyed3
from html2text import html2text
from progress.bar import Bar
from bs4 import BeautifulSoup

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

# Get the previous music list path
previouspath = os.path.join(cwdir, "previous.pickle")

# Get the list of all previous music ids
if os.path.exists(previouspath):
    with open(previouspath, 'rb') as file:
        musiclist = pickle.load(file)
else:
    musiclist = []

defaultimageurl = "img.ngfiles.com/defaults/icon-audio.png"

def fuck():
    global title, artist, comment, genre, releasedate, imageurl, contact, ngurl

    # Set the url for requesting
    ngurl = f"https://newgrounds.com/audio/listen/{id}"
    try:
        # Request the content
        content = requests.get(ngurl)
        soup = BeautifulSoup(content.text, 'html.parser')

        # Check if you are living in Turkey / I still don't understand why it's blocked
        if "Bilgi Teknolojileri" in soup.title.text:
            print()
            print("whyyyyyyyyyyyyyyyyyy :(((((((")


        # Get metadata
        title = soup.title.text
        artist = soup.find("div", {"class": "item-details-main"}).contents[1].contents[1].text
        comment = soup.find(id="author_comments").text
        genre = soup.find(attrs={"data-genre-for": True}).text
        releasedate = soup.find(id="sidestats").contents[5].contents[3].text[-4:]
        imageurl = f"https://aicon.ngfiles.com/{int(id)//1000}/{id}.png"

        contact = True
        time.sleep(2)

    except requests.exceptions.ConnectionError:
        time.sleep(4)
        # Fuck
        print("fuck")
        fuck()

    except:
        print( sys.exc_info()[0])
        # The music is deleted or removed
        contact = False

        # Get file locations
        cachefile = os.path.join(cachedir, f"{id}.mp3")
        musicfile = os.path.join(musicdir, f"Unknown [{id}].mp3")

        imageurl = defaultimageurl

        # Copy the music file to the directory
        copy(cachefile, musicfile)

        # Create mp3 tag
        tag = id3.tag.Tag()
        tag.parse(musicfile)
        tag.header.version = id3.ID3_V2_3

        fuck2()

        # Save the tag
        tag.save(encoding="utf-8")

def fuck2():
    global imageurl, imagedata, tag
    try:
        # Get image data
        response = requests.get(imageurl)
        imagedata = response.content

        # Set image data
        tag.images.set(type_=3, img_data=imagedata, mime_type="image/png")
        time.sleep(2)

    except requests.exceptions.ConnectionError:
        time.sleep(4)
        # Fuck 2
        print("fuck2")
        fuck2()
    except:
        imageurl = defaultimageurl
        fuck2()

# Do for each id
for id in idlist:

    # Check if already exists
    if id not in musiclist:

        fuck()

        if contact:

            # Remove special characters from title
            title = re.sub('[<>:"/\\|?*]', "", title)

            # Set year
            year = eyed3.core.Date(int(releasedate))

            # Get file locations
            cachefile = os.path.join(cachedir, f"{id}.mp3")
            musicfile = os.path.join(musicdir, f"{title} [{id}].mp3")

            # Check if file already exists
            if not os.path.exists(musicfile):
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

            fuck2()

            # Save the tag
            tag.save(encoding="utf-8")


    bar.next()

# Update previous music ID list
musiclist += [re.findall("\\[\\d+\\]", f)[0][1:-1] for f in os.listdir(musicdir) if f[:7] != "Unknown" and f[-4:] == ".mp3"]

# Write the list to the file
with open(previouspath, 'wb') as file:
    pickle.dump(musiclist, file)

print(f"\nFinished, saved to {musicdir}")
