#!/usr/bin/env python
# coding=UTF8

# tune2tube.py
#
# Copyright 2014 Michiel Sikma
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.
#
# This script contains code from <https://developers.google.com/>.

__author__ = 'Michiel Sikma <michiel@letsdeliver.com>'

import argparse
import subprocess
import sys
import re
import os
import httplib
import httplib2
import random
import time
import mutagen
import itertools

from datetime import datetime, timedelta
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets, AccessTokenRefreshError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# ffmpeg is a dependency for this script. ffprobe should be
# installed along with ffmpeg.
PATH_FFMPEG = 'ffmpeg'
PATH_FFPROBE = 'ffprobe'

# Version--todo: change to commit number
T2T_VERSION = '0.1'

# Image and audio input files.
IN_IMAGE = ''
IN_AUDIO = ''

# Self-reference for debugging feedback.
THIS_FILE = os.path.basename(__file__)

# Temporary output filename. We use MKV as container because MP4 doesn't
# support FLAC audio.
PATH_OUTPUT = 'tmp.mkv'

# Whether to display ffmpeg/ffprobe output.
VERBOSE = False

# Whether to only generate the video file without uploading it.
GENERATE_ONLY = False

# Whether to forego the usage of stored oauth2 tokens.
# If set to True, you will need to authenticate using your browser
# each time you use the script.
NO_STORED_AUTH = False

# A list of MP3/OGG/ASF/MP4/APE tags that we might encounter.
TAGS_COMMON = ['album', 'title', 'artist', 'album-artist', 'release-date', 'release-date', 'original-release-date', 'composer', 'lyricist', 'writer', 'conductor', 'performer', 'remixer', 'arranger', 'engineer', 'producer', 'mix-dj', 'mixer', 'grouping', 'subtitle', 'disc-subtitle', 'track-number', 'total-tracks', 'disc-number', 'total-discs', 'compilation-itunes', 'comment', 'comments', 'genre', 'bpm', 'mood', 'isrc', 'copyright', 'lyrics', 'media', 'record-label', 'catalog-number', 'barcode', 'encoded-by', 'encoder-settings', 'album-sort-order', 'album-artist-sort-order', 'artist-sort-order', 'title-sort-order', 'composer-sort-order', 'show-name-sort-order', 'asin', 'gapless-playback', 'podcast', 'podcast-url', 'show-name', 'script', 'language', 'license', 'original-year', 'acoustid', 'acoustid-fingerprint', 'website', 'work-title', 'website', 'original-artist']
TAGS_DB = {
    'ID3v23':
        ['TALB', 'TIT2', 'TPE1', 'TPE2', 'TYER', 'TDAT', 'TORY', 'TCOM', 'TEXT', 'TXXX:Writer', 'TPE3', 'IPLS:instrument', 'TPE4', 'IPLS:arranger', 'IPLS:engineer', 'IPLS:producer', 'IPLS:DJ-mix', 'IPLS:mix', 'TIT1', 'TIT3', '', 'TRCK', 'TRCK', 'TPOS', 'TPOS', 'TCMP', 'COMM:description', 'TCON', 'TBPM', '', 'TSRC', 'TCOP', 'USLT:description', 'TMED', 'TPUB', 'TXXX:CATALOGNUMBER', 'TXXX:BARCODE', 'TENC', 'TSSE', 'TSOA', 'TSO2', 'TSOP', 'TSOT', 'TSOC', '', 'TXXX:ASIN', '', '', '', '', 'TXXX:SCRIPT', 'TLAN', 'WCOPTXXX:LICENSE', 'TXXX:originalyear', 'TXXX:Acoustid Id', 'TXXX:Acoustid Fingerprint', 'WOAR', 'TOAL', 'WXXX:website', 'TOPE'],
    'ID3v24':
        ['TALB', 'TIT2', 'TPE1', 'TPE2', 'TDRC', 'TDRC', 'TDOR', 'TCOM', 'TEXT', 'TXXX:Writer', 'TPE3', 'TMCL:instrument', 'TPE4', 'TIPL:arranger', 'TIPL:engineer', 'TIPL:producer', 'TIPL:DJ-mix', 'TIPL:mix', 'TIT1', 'TIT3', 'TSST', 'TRCK', 'TRCK', 'TPOS', 'TPOS', 'TCMP', 'COMM:description', 'TCON', 'TBPM', 'TMOO', 'TSRC', 'TCOP', 'USLT:description', 'TMED', 'TPUB', 'TXXX:CATALOGNUMBER', 'TXXX:BARCODE', 'TENC', 'TSSE', 'TSOA', 'TXXX:ALBUMARTISTSORT', 'TSOP', 'TSOT', 'TXXX:COMPOSERSORT', '', 'TXXX:ASIN', '', '', '', '', 'TXXX:SCRIPT', 'TLAN', 'WCOPTXXX:LICENSE', 'TXXX:originalyear', 'TXXX:Acoustid Id', 'TXXX:Acoustid Fingerprint', 'WOAR', 'TOAL', 'WXXX:website', 'TOPE'],
    'ASF/Windows Media':
        ['WM/AlbumTitle', 'Title', 'Author', 'WM/AlbumArtist', 'WM/Year', 'WM/Year', 'WM/OriginalReleaseYear', 'WM/Composer', 'WM/Writer', '', 'WM/Conductor', '', 'WM/ModifiedBy', '', 'WM/Engineer', 'WM/Producer', 'WM/DJMixer', 'WM/Mixer', 'WM/ContentGroupDescription', 'WM/SubTitle', 'WM/SetSubTitle', 'WM/TrackNumber', '', 'WM/PartOfSet', '', 'WM/IsCompilation', 'Description', 'WM/Genre', 'WM/BeatsPerMinute', 'WM/Mood', 'WM/ISRC', 'Copyright', 'WM/Lyrics', 'WM/Media', 'WM/Publisher', 'WM/CatalogNo', 'WM/Barcode', 'WM/EncodedBy', 'WM/EncoderSettings', 'WM/AlbumSortOrder', 'WM/AlbumArtistSortOrder', 'WM/ArtistSortOrder', 'WM/TitleSortOrder', 'WM/ComposerSortOrder', '', '', '', '', '', '', 'WM/Script', 'WM/Language', 'LICENSE', '', 'Acoustid/Id', 'Acoustid/Fingerprint', '', '', '', ''],
    'iTunes MP4':
        ['©alb', '©nam', '©ART', 'aART', '©day', '©day', '', '©wrt', '----:com.apple.iTunes:LYRICIST', '', '----:com.apple.iTunes:CONDUCTOR', '', '----:com.apple.iTunes:REMIXER', '', '----:com.apple.iTunes:ENGINEER', '----:com.apple.iTunes:PRODUCER', '----:com.apple.iTunes:DJMIXER', '----:com.apple.iTunes:MIXER', '©grp', '----:com.apple.iTunes:SUBTITLE', '----:com.apple.iTunes:DISCSUBTITLE', 'trkn', 'trkn', 'disk', 'disk', 'cpil', '©cmt', '©gen', 'tmpo', '----:com.apple.iTunes:MOOD', '----:com.apple.iTunes:ISRC', 'cprt', '©lyr', '----:com.apple.iTunes:MEDIA', '----:com.apple.iTunes:LABEL', '----:com.apple.iTunes:CATALOGNUMBER', '----:com.apple.iTunes:BARCODE', '©too', '', 'soal', 'soaa', 'soar', 'sonm', 'soco', 'sosn', '----:com.apple.iTunes:ASIN', 'pgap', 'pcst', 'purl', 'tvsh', '----:com.apple.iTunes:SCRIPT', '----:com.apple.iTunes:LANGUAGE', '----:com.apple.iTunes:LICENSE', '', '----:com.apple.iTunes:Acoustid Id', '----:com.apple.iTunes:Acoustid Fingerprint', '', '', '', ''],
    'Vorbis':
        ['ALBUM', 'TITLE', 'ARTIST', 'ALBUMARTIST', 'DATE', 'DATE', 'ORIGINALDATE', 'COMPOSER', 'LYRICIST', 'WRITER', 'CONDUCTOR', 'PERFORMERinstrument', 'REMIXER', 'ARRANGER', 'ENGINEER', 'PRODUCER', 'DJMIXER', 'MIXER', 'GROUPING', 'SUBTITLE', 'DISCSUBTITLE', 'TRACKNUMBER', 'TRACKTOTAL and    TOTALTRACKS', 'DISCNUMBER', 'DISCTOTAL and TOTALDISCS', 'COMPILATION', 'COMMENT', 'COMMENTS', 'GENRE', 'BPM', 'MOOD', 'ISRC', 'COPYRIGHT', 'LYRICS', 'MEDIA', 'LABEL', 'CATALOGNUMBER', 'BARCODE', 'ENCODEDBY', 'ENCODERSETTINGS', 'ALBUMSORT', 'ALBUMARTISTSORT', 'ARTISTSORT', 'TITLESORT', 'COMPOSERSORT', '', 'ASIN', '', '', '', '', 'SCRIPT', 'LANGUAGE', 'LICENSE', 'ORIGINALYEAR', 'ACOUSTID_ID', 'ACOUSTID_FINGERPRINT', 'WEBSITE', 'WORK', '', ''],
    'APEv2':
        ['Album', 'Title', 'Artist', 'Album Artist', 'Year', 'Year', '', 'Composer', 'Lyricist', 'Writer', 'Conductor', 'Performerinstrument', 'MixArtist', 'Arranger', 'Engineer', 'Producer', 'DJMixer', 'Mixer', 'Grouping', 'Subtitle', 'DiscSubtitle', 'Track', 'Track', 'Disc', 'Disc', 'Compilation', 'Comment', 'Comments', 'Genre', 'BPM', 'Mood', 'ISRC', 'Copyright', 'Lyrics', 'Media', 'Label', 'CatalogNumber', 'Barcode', 'EncodedBy', 'EncoderSettings', 'ALBUMSORT', 'ALBUMARTISTSORT', 'ARTISTSORT', 'TITLESORT', 'COMPOSERSORT', '', 'ASIN', '', '', '', '', 'Script', 'Language', 'LICENSE', 'ORIGINALYEAR', 'ACOUSTID_ID', 'ACOUSTID_FINGERPRINT', 'Weblink', 'WORK', '', ''],
}
TAGS_DB['common'] = TAGS_COMMON
# Full list of all the aforementioned, for lookup.
TAGS_ALL = {}
for type in TAGS_DB:
    for n in range(len(TAGS_DB[type])):
        # If these are iTunes tags, ignore the colons.
        # Otherwise, save only the part before the colon.
        item = TAGS_DB[type][n]
        if not 'iTunes' in item:
            item = item.split(':')[0]
        TAGS_ALL[item] = n

TAGS_READABLE = ['Album', 'Title', 'Artist', 'Album Artist', 'Release Date', 'Release Date', 'Original Release Date', 'Composer', 'Lyricist', 'Writer', 'Conductor', 'Performer', 'Remixer', 'Arranger', 'Engineer', 'Producer', 'Mix-DJ', 'Mixer', 'Grouping', 'Subtitle', 'Disc Subtitle', 'Track Number', 'Total Tracks', 'Disc Number', 'Total Discs', 'Compilation (iTunes)', 'Comment', 'Comment', 'Genre', 'BPM', 'Mood', 'ISRC', 'Copyright', 'Lyrics', 'Media', 'Record Label', 'Catalog Number', 'Barcode', 'Encoded By', 'Encoder Settings', 'Album Sort Order', 'Album Artist Sort Order', 'Artist Sort Order', 'Title Sort Order', 'Composer Sort Order', 'Show Name Sort Order', 'ASIN', 'Gapless Playback', 'Podcast', 'Podcast URL', 'Show Name', 'Script', 'Language', 'License', 'Original Year', 'AcoustID', 'AcoustID Fingerprint', 'Website', 'Work Title', 'Website', 'Original Artist']

# Lookup function that translates any system's tag (e.g. ID3v2's TLAN or 
# Vorbis's ALBUMARTISTSORT) into a human-readable string.
def tag_lookup(tag, human_readable=False):
    tag_key = tag.split(':')[0]
    try:
        tag_code = TAGS_ALL[tag_key] % len(TAGS_READABLE)
        if human_readable:
            return TAGS_READABLE[tag_code]
        else:
            return TAGS_COMMON[tag_code]
    except:
        return tag

# Default title to use in case the user's own title is an empty string.
DEFAULT_TITLE = '(Empty title)'

# Default variables to use for the dynamically generated title.
DEFAULT_TITLE_VARS = 'artist,title'

# Whether to use the dynamically generated title from the file's metadata.
DYNAMIC_TITLE = False

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error, IOError, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine
)
  
# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# We can set our uploaded video to one of these statuses.
VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')

CURRENT_DATETIME = str(datetime.utcnow())

# Set up our command line argument parser.
# The argparser is initialized in oauth2client/tools.py. We're just
# adding our own arguments to the ones already defined there.
argparser.description = 'Generates a video from an image and audio file and uploads it to Youtube.'
argparser.epilog = 'A Youtube Data API client key is required to use this script, as well as ffmpeg. For help on setting up these dependencies, see this project\'s Github page <http://github.com/msikma/tune2tube/> or the included README file.'
argparser.add_help = True
# Manually add a help argument, as it is turned off in oauth2client/tools.py.
argparser.add_argument('--no_stored_auth', action='store_true', help='Forego using stored oauth2 tokens.')
argparser.add_argument('audio_file', help='Audio file (MP3, OGG, FLAC, etc).')
argparser.add_argument('image_file', help='Image file (PNG, JPG, etc).')
argparser.add_argument('--output', help='Save the output video (.MP4) to a file rather than uploading it to Youtube.')
argparser.add_argument('--cs_json', help='Path to the client secrets json file (default: client_secrets.json).', default='client_secrets.json')
argparser.add_argument('--privacy', choices=VALID_PRIVACY_STATUSES, help='Privacy status of the video (default: unlisted).', default='unlisted')
argparser.add_argument('--category', default='10', help='Numeric video category (see the Github wiki for a list; the default is 10, Music).')
argparser.add_argument('--keywords', help='Comma-separated list of video keywords/tags.', default='')
mxgroup = argparser.add_mutually_exclusive_group()
mxgroup.add_argument('--title', help='Video title string (default: \'%s\'). If neither --title nor --title_vars is specified, --title_vars will be used with its default value, unless this would result in an empty title.' % DEFAULT_TITLE)
mxgroup.add_argument('--title_vars', nargs='?', help='Comma-separated list of metadata variables to use as the video title (default: %s).' % DEFAULT_TITLE_VARS)
argparser.add_argument('--title_sep', help='Separator for the title variables (default: \' - \', yielding e.g. \'Artist - Title\'). Ignored if using --title_str.', default=' - ')
argparser.add_argument('--description', nargs='?', help='Video description string (default: empty string).', default='')
argparser.add_argument('--add_metadata', action='store_true', help='Adds a list of audio file metadata to the description (default: True).', default=True)
argparser.add_argument('-V', '--version', action='version', version='%(prog)s '+T2T_VERSION, help='Show version number and exit.')
mxgroup = argparser.add_mutually_exclusive_group()
mxgroup.add_argument('-v', '--verbose', action='store_true', help='Verbose mode (display ffmpeg/ffprobe output).')
mxgroup.add_argument('-q', '--quiet', action='store_true', help='Quiet mode.')
argparser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit.')

args = argparser.parse_args()

# From here we can assume we have our required arguments.
if args.verbose:
    VERBOSE = True
IN_IMAGE = args.image_file
IN_AUDIO = args.audio_file

# Decide whether to go with the standard title or the metadata title.
if args.title is None and args.title_vars is None:
    DYNAMIC_TITLE = True
    args.title_vars = DEFAULT_TITLE_VARS
if args.title_vars is not None:
    DYNAMIC_TITLE = True
if args.title_vars is None:
    args.title_vars = ''
if args.description is None:
    args.description = ''
if args.cs_json:
    CLIENT_SECRETS_FILE = args.cs_json
if args.no_stored_auth:
    NO_STORED_AUTH = True
if args.output:
    GENERATE_ONLY = True
    PATH_OUTPUT = args.output

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = '''
%s: Error: Please configure OAuth 2.0.

To make this script run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console, which can be accessed
through <https://console.developers.google.com/>. See the README file
for more details.
''' % (THIS_FILE, os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE)))

probe_cmd = [PATH_FFPROBE, IN_AUDIO];

# Formats bytes in a human-readable manner.
# Recipe by Giampaolo Rodola <g.rodola[AT]gmail[DOT]com>, slightly modified.
# Found on <http://goo.gl/Ldo93T>, MIT license.
def bytes2human(n, format='%(value).1f %(symbol)s', symbols='customary'):
    """Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs
    """
    vocab = {
        'customary'     : ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'),
        'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                           'zetta', 'iotta'),
        'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
        'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                           'zebi', 'yobi'),
    }
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = vocab[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

# Get authenticated and cache the result.
def get_authenticated_service(args):
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        scope = YOUTUBE_UPLOAD_SCOPE,
        message = MISSING_CLIENT_SECRETS_MESSAGE
    )
    
    storage = Storage('%s-oauth2.json' % THIS_FILE)
    credentials = storage.get()
    if credentials is None or credentials.invalid or NO_STORED_AUTH:
        credentials = run_flow(flow, storage, args)
    
    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http = credentials.authorize(httplib2.Http())
    )

# Begin a resumable video upload.
def initialize_upload(youtube, args, file):
    tags = None
    
    if args.keywords:
        tags = args.keywords.split(',')
    
    # If we need to generate a dynamic title, do so now.
    if DYNAMIC_TITLE:
        title_vars = args.title_vars.split(',')
        items = [args.metadata[n] for n in title_vars if n in args.metadata]
        title = args.title_sep.join(items)
    else:
        title = args.title
    
    # Add the metadata tags to the description if needed.
    description = args.description.strip()
    if args.add_metadata:
        if description is not '':
            description = description+'\n'
        # Sort the list of metadata, so that items with linebreaks go last.
        metalist = [{key: args.metadata[key]} for key in args.metadata]
        metalist = sorted(metalist, key=lambda x: '\n' in list(x.values())[0])
        for tag in metalist:
            for key in tag:
                value = tag[key]
                nice_key = tag_lookup(key, True)
                if '\n' in value:
                    description += '\n----\n%s: %s\n' % (nice_key, value)
                else:
                    description += '\n%s: %s' % (nice_key, value)
    
    body = dict(
        snippet = dict(
            title = title,
            description = description,
            tags = tags,
            categoryId = args.category
        ),
        status = dict(
            privacyStatus = args.privacy
        )
    )
    
    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part = ','.join(body.keys()),
        body = body,
        media_body = MediaFileUpload(file, chunksize=-1, resumable=True)
    )
    
    filesize = os.path.getsize(file)
    print('Uploading file... (filesize: %s)' % bytes2human(filesize))
    resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print("Video ID `%s' was successfully uploaded. Its visibility is set to `%s'." % (response['id'], args.privacy))
                print('URL of the newly uploaded video: <https://www.youtube.com/watch?v=%s>' % response['id'])
                print('It may take some time for the video to finish processing; typically 1-10 minutes.')
            else:
                error_exit('The upload failed with an unexpected response: %s' % response)
        except HttpError, e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS, e:
            error = 'A retriable error occurred: %s' % e
            
        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                error_exit('Too many upload errors. No longer attempting to retry.')
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print('Sleeping %f seconds and then retrying...' % sleep_seconds)
            time.sleep(sleep_seconds)

def error_exit(str):
    print('%(prog)s: Error: %(str)s' % {'str': str, 'prog': THIS_FILE})
    exit()

if __name__ == '__main__':
    # Now beginning the main program logic.
    # Check to see if our files exist at all.
    if not (os.path.exists(IN_IMAGE) and os.path.exists(IN_AUDIO)):
        error_exit('Please specify a valid image and audio file.')
    
    print('%s %s' % (THIS_FILE, T2T_VERSION))
    
    # Check our MP3/OGG/FLAC/etc file and get its duration.
    try:
        probe_out = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
        if VERBOSE:
            print(probe_out)
    except:
        error_exit("Couldn't probe the audio file. ffprobe might not be available. Make sure ffmpeg is installed.")
    
    # Try to extract some metadata from the file using Mutagen.
    try:
        metadata = mutagen.File(IN_AUDIO)
    except AttributeError:
        metadata = []
    
    # Save a human-readable version of the metadata in the object.
    # Keep the original Mutagen output around too.
    args.metadata = {}
    args.orig_metadata = metadata
    for tag in metadata:
        item = metadata[tag]
        # We join the item in case it's still a list, as in the case
        # of Vorbis.
        if isinstance(item, (list, tuple)):
            item = ''.join(item)
        args.metadata[tag_lookup(tag)] = str(item)
    
    # Lift the actual track duration string out of the output.
    duration = re.findall('Duration: (.+?),', probe_out)

    # If we get valid output, parse the duration and get a seconds value.
    # Otherwise, stop the script.
    if len(duration):
        duration = duration[0]
    else:
        error_exit("Couldn't parse ffprobe's output. Try again with -v (--verbose) to see what went wrong.")

    # Turn the string into a datetime format.
    try:
        audio_info = datetime.strptime(duration, '%H:%M:%S.%f')
        delta = timedelta(
            hours = audio_info.hour,
            minutes = audio_info.minute,
            seconds = audio_info.second,
            microseconds = audio_info.microsecond
        )
    except ValueError:
        error_exit('Encountered an error trying to determine the duration of the audio file. It could be in an unrecognized format, or longer than 24 hours. (Duration: %s, exception: %s)' % (duration, sys.exc_info()[0]))

    print('Using image file `%s\', size: %s.' % (IN_IMAGE, os.path.getsize(IN_IMAGE)))
    print('Using audio file `%s\', size: %s, duration: %s.' % (IN_AUDIO, os.path.getsize(IN_AUDIO), duration))
    
    if args.metadata == []:
        print("Couldn't extract audio file tags. Continuing.")
    else:
        print('Extracted %d tag(s) from the audio file.' % len(args.metadata))
    
    print('Encoding video file...')
    
    # Now call ffmpeg and produce the video.
    ffmpeg_cmd = [PATH_FFMPEG,
        # loop the video (picture) for the movie's duration
        '-loop', '1',
        # a framerate of 1fps (anything lower won't be accepted by Youtube)
        '-framerate', '1:1',
        # one input file is the picture
        '-i', IN_IMAGE,
        # one input file is the audio
        '-i', IN_AUDIO,
        # only copy the audio, don't re-encode it
        '-c:a', 'copy',
        # duration of the video
        '-t', str(delta.total_seconds()),
        # automatically overwrite on duplicate
        '-y',
        # use x264 as the video encoder
        '-c:v', 'libx264',
        # 4:4:4 chroma subsampling (best quality)
        '-pix_fmt', 'yuv444p',
        # as fast as possible, at cost of filesize (uploading costs less time)
        '-preset', 'ultrafast',
        # lossless quality
        '-qp', '0',
        # output
        PATH_OUTPUT
    ]
    try:
        probe_out = subprocess.check_output(ffmpeg_cmd, stderr=subprocess.STDOUT)
        if VERBOSE:
            print(probe_out)
    except:
        error_exit('Encountered an error trying to generate the video. Try again with -v (--verbose) to see what went wrong. (Exception: %s)' % sys.exc_info()[0])
    
    print('Successfully generated the file `%s\'.' % PATH_OUTPUT)
    if GENERATE_ONLY:
        print('Skipping Youtube upload.')
        exit()
    
    # Now upload the file to Youtube.
    print('Authenticating using the Youtube API...')
    youtube = get_authenticated_service(args)
    try:
        initialize_upload(youtube, args, PATH_OUTPUT)
    except HttpError, e:
        print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
    except AccessTokenRefreshError, e:
        print('The stored access token seems to be invalid. Delete any -oauth2.json files that may exist and try again, or try again with the --no_stored_auth switch.')
