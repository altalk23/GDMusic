import os
import sys
import requests
import time
import re
import pickle
from shutil import copy
from eyed3 import id3
import eyed3
from progress.bar import Bar
from bs4 import BeautifulSoup


def setup():
    # Get directories
    cwdir = os.getcwd()
    homedir = os.path.expanduser("~")

    # Create the music directory if not exists
    global musicdir
    musicdir = os.path.join(cwdir, "music")
    if not os.path.exists(musicdir):
        os.mkdir(musicdir)

    # Get the cache directory
    if sys.platform == "darwin":
        global cachedir
        cachedir = os.path.join(homedir, "Library", "Caches")
    else:
        raise NotImplementedError

    # Get the path of all previous music ids
    global previouspath
    previouspath = os.path.join(cwdir, "previous.pickle")

    # Get the list of all previous music ids
    global prevlist
    if os.path.exists(previouspath):
        with open(previouspath, 'rb') as file:
            prevlist = pickle.load(file)
    else:
        prevlist = []

    # Get the list of all music ids
    global musiclist
    musiclist = [
        f[:-4]
        for f in os.listdir(cachedir)
        if f[-4:] == ".mp3" and f[:-4] not in prevlist
    ]

    # Create a progress bar
    global bar
    bar = Bar('Extracting', fill='█', max=len(musiclist))

    # Disable tagger warnings
    eyed3.log.setLevel("ERROR")

def getContent(url):
    # Try
    while True:
        try:
            # Request the content
            response = requests.get(url)

            # Return the content
            return response.content
        except requests.exceptions.ConnectionError:
            # Sleep and try again
            time.sleep(4)

def getSongMetadata(id):

    # Request the content
    content = getContent(f"https://newgrounds.com/audio/listen/{id}")

    # Parse the content
    soup = BeautifulSoup(content, 'html.parser')

    # Check if you are living in Turkey
    if "Bilgi Teknolojileri" in soup.title.text:
        raise Exception("Open your VPN")

    # Check if the submission is removed
    if "Whoops, that's a swing and a miss!" in soup.title.text:
        # Set defaults
        intact = False
        imageurl = "https://img.ngfiles.com/defaults/icon-audio.png"

        return {
            "intact": intact,
            "title": "Unknown",
            "imageurl": imageurl
        }

    else:
        intact = True

        # Get metadata
        title = soup.title.text
        artist = soup.find("div", {"class": "item-details-main"}).contents[1].contents[1].text
        comment = soup.find(id="author_comments").text
        genre = soup.find(attrs={"data-genre-for": True}).text
        year = soup.find(id="sidestats").contents[5].contents[3].text[-4:]
        imageurl = soup.find(property="og:image")["content"]

        return {
            "intact": intact,
            "title": title,
            "artist": artist,
            "comment": comment,
            "genre": genre,
            "year": year,
            "imageurl": imageurl
        }

def copySong(id, data):
    # Get file locations
    cachefile = os.path.join(cachedir, f"{id}.mp3")
    musicfile = os.path.join(musicdir, f"{data['title']} [{id}].mp3")

    # Check if file already exists
    if not os.path.exists(musicfile):
        # Copy the music file to the directory
        copy(cachefile, musicfile)

def editSongMetadata(id, data):
    # Remove special characters from title
    data["title"] = re.sub('[<>:"/\\|?*]', "", data["title"])

def setSongMetadata(id, data, tag):

    # Set tag values
    tag.artist = data["artist"]
    tag.title = data["title"]
    tag.album = f"{data['title']} [{id}]"
    tag.genre = data["genre"]
    tag.recording_date = eyed3.core.Date(int(data["year"]))
    tag.comments.set(data["comment"])

def setSongImage(id, data, tag):
    # Request the content
    content = getContent(data["imageurl"])

    # Set image data
    tag.images.set(type_=3, img_data=content, mime_type="image/png")

def updateSongMetadata(id):
    # Get song metadata from newgrounds
    data = getSongMetadata(id)

    if data["intact"]:
        editSongMetadata(id, data)

    copySong(id, data)

    # Create mp3 tag
    tag = id3.tag.Tag()
    tag.parse(os.path.join(musicdir, f"{data['title']} [{id}].mp3"))
    tag.header.version = id3.ID3_V2_3

    if data["intact"]:
        setSongMetadata(id, data, tag)

    setSongImage(id, data, tag)

    # Save the mp3 tag
    tag.save(encoding="utf-8")

def finish():
    # Update previous music ID list
    global musiclist
    global prevlist
    prevlist += musiclist

    # Write the list to the file
    with open(previouspath, 'wb') as file:
        pickle.dump(prevlist, file)

setup()

for music in musiclist:
    updateSongMetadata(music)
    bar.next()

finish()
print(f"\nFinished, saved to {musicdir}")
