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
#
# Sorry for the lack of pep8, this will be fixed in some future version.

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
import pprint

from datetime import datetime, timedelta
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets, AccessTokenRefreshError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


this_file = os.path.basename(__file__)


# Formats bytes in a human-readable manner.
# Recipe by Giampaolo Rodola <g.rodola[AT]gmail[DOT]com>, slightly modified.
# Found on <http://goo.gl/Ldo93T>, MIT license.
def bytes2human(n, format='%(value).1f %(symbol)s', symbols='customary'):
    '''
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs
    '''
    vocab = {
        'customary'     : ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'),
        'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta'),
        'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'),
        'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi'),
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


# Used in case of an error.
def error_exit(str='unknown error'):
    '''
    Exits the program with an error message.
    '''
    print('%(prog)s: error: %(str)s' % {'str': str, 'prog': this_file})
    exit()


class TuneTags(object):
    '''
    Used to look up and normalize tags in audio files.
    Contains a dict with tag key names for various file formats.
    The keys are linked to a list of human-readable labels.
    '''
    def __init__(self):
        # A list of MP3/OGG/ASF/MP4/APE tags that we might encounter.
        self.tags_common = [
            'album', 'title', 'artist', 'album-artist', 'release-date', 'release-date', 'original-release-date', 'composer', 'lyricist', 'writer', 'conductor', 'performer', 'remixer', 'arranger', 'engineer', 'producer', 'mix-dj', 'mixer', 'grouping', 'subtitle', 'disc-subtitle', 'track-number', 'total-tracks', 'disc-number', 'total-discs', 'compilation-itunes', 'comment', 'comments', 'genre', 'bpm', 'mood', 'isrc', 'copyright', 'lyrics', 'media', 'record-label', 'catalog-number', 'barcode', 'encoded-by', 'encoder-settings', 'album-sort-order', 'album-artist-sort-order', 'artist-sort-order', 'title-sort-order', 'composer-sort-order', 'show-name-sort-order', 'asin', 'gapless-playback', 'podcast', 'podcast-url', 'show-name', 'script', 'language', 'license', 'original-year', 'acoustid', 'acoustid-fingerprint', 'website', 'work-title', 'website', 'original-artist', 'date', 'tracknumber'
        ]
        self.tags_db = {
            'ID3v23': [
                'TALB', 'TIT2', 'TPE1', 'TPE2', 'TYER', 'TDAT', 'TORY', 'TCOM', 'TEXT', 'TXXX:Writer', 'TPE3', 'IPLS:instrument', 'TPE4', 'IPLS:arranger', 'IPLS:engineer', 'IPLS:producer', 'IPLS:DJ-mix', 'IPLS:mix', 'TIT1', 'TIT3', '', 'TRCK', 'TRCK', 'TPOS', 'TPOS', 'TCMP', 'COMM:description', 'TCON', 'TBPM', '', 'TSRC', 'TCOP', 'USLT:description', 'TMED', 'TPUB', 'TXXX:CATALOGNUMBER', 'TXXX:BARCODE', 'TENC', 'TSSE', 'TSOA', 'TSO2', 'TSOP', 'TSOT', 'TSOC', '', 'TXXX:ASIN', '', '', '', '', 'TXXX:SCRIPT', 'TLAN', 'WCOPTXXX:LICENSE', 'TXXX:originalyear', 'TXXX:Acoustid Id', 'TXXX:Acoustid Fingerprint', 'WOAR', 'TOAL', 'WXXX:website', 'TOPE', '', ''
            ],
            'ID3v24': [
                'TALB', 'TIT2', 'TPE1', 'TPE2', 'TDRC', 'TDRC', 'TDOR', 'TCOM', 'TEXT', 'TXXX:Writer', 'TPE3', 'TMCL:instrument', 'TPE4', 'TIPL:arranger', 'TIPL:engineer', 'TIPL:producer', 'TIPL:DJ-mix', 'TIPL:mix', 'TIT1', 'TIT3', 'TSST', 'TRCK', 'TRCK', 'TPOS', 'TPOS', 'TCMP', 'COMM:description', 'TCON', 'TBPM', 'TMOO', 'TSRC', 'TCOP', 'USLT:description', 'TMED', 'TPUB', 'TXXX:CATALOGNUMBER', 'TXXX:BARCODE', 'TENC', 'TSSE', 'TSOA', 'TXXX:ALBUMARTISTSORT', 'TSOP', 'TSOT', 'TXXX:COMPOSERSORT', '', 'TXXX:ASIN', '', '', '', '', 'TXXX:SCRIPT', 'TLAN', 'WCOPTXXX:LICENSE', 'TXXX:originalyear', 'TXXX:Acoustid Id', 'TXXX:Acoustid Fingerprint', 'WOAR', 'TOAL', 'WXXX:website', 'TOPE', '', ''
            ],
            'ASF/Windows Media': [
                'WM/AlbumTitle', 'Title', 'Author', 'WM/AlbumArtist', 'WM/Year', 'WM/Year', 'WM/OriginalReleaseYear', 'WM/Composer', 'WM/Writer', '', 'WM/Conductor', '', 'WM/ModifiedBy', '', 'WM/Engineer', 'WM/Producer', 'WM/DJMixer', 'WM/Mixer', 'WM/ContentGroupDescription', 'WM/SubTitle', 'WM/SetSubTitle', 'WM/TrackNumber', '', 'WM/PartOfSet', '', 'WM/IsCompilation', 'Description', 'WM/Genre', 'WM/BeatsPerMinute', 'WM/Mood', 'WM/ISRC', 'Copyright', 'WM/Lyrics', 'WM/Media', 'WM/Publisher', 'WM/CatalogNo', 'WM/Barcode', 'WM/EncodedBy', 'WM/EncoderSettings', 'WM/AlbumSortOrder', 'WM/AlbumArtistSortOrder', 'WM/ArtistSortOrder', 'WM/TitleSortOrder', 'WM/ComposerSortOrder', '', '', '', '', '', '', 'WM/Script', 'WM/Language', 'LICENSE', '', 'Acoustid/Id', 'Acoustid/Fingerprint', '', '', '', '', '', ''
            ],
            'iTunes MP4': [
                '©alb', '©nam', '©ART', 'aART', '©day', '©day', '', '©wrt', '----:com.apple.iTunes:LYRICIST', '', '----:com.apple.iTunes:CONDUCTOR', '', '----:com.apple.iTunes:REMIXER', '', '----:com.apple.iTunes:ENGINEER', '----:com.apple.iTunes:PRODUCER', '----:com.apple.iTunes:DJMIXER', '----:com.apple.iTunes:MIXER', '©grp', '----:com.apple.iTunes:SUBTITLE', '----:com.apple.iTunes:DISCSUBTITLE', 'trkn', 'trkn', 'disk', 'disk', 'cpil', '©cmt', '©gen', 'tmpo', '----:com.apple.iTunes:MOOD', '----:com.apple.iTunes:ISRC', 'cprt', '©lyr', '----:com.apple.iTunes:MEDIA', '----:com.apple.iTunes:LABEL', '----:com.apple.iTunes:CATALOGNUMBER', '----:com.apple.iTunes:BARCODE', '©too', '', 'soal', 'soaa', 'soar', 'sonm', 'soco', 'sosn', '----:com.apple.iTunes:ASIN', 'pgap', 'pcst', 'purl', 'tvsh', '----:com.apple.iTunes:SCRIPT', '----:com.apple.iTunes:LANGUAGE', '----:com.apple.iTunes:LICENSE', '', '----:com.apple.iTunes:Acoustid Id', '----:com.apple.iTunes:Acoustid Fingerprint', '', '', '', '', '', ''
            ],
            'Vorbis': [
                'ALBUM', 'TITLE', 'ARTIST', 'ALBUMARTIST', 'DATE', 'DATE', 'ORIGINALDATE', 'COMPOSER', 'LYRICIST', 'WRITER', 'CONDUCTOR', 'PERFORMER', 'REMIXER', 'ARRANGER', 'ENGINEER', 'PRODUCER', 'DJMIXER', 'MIXER', 'GROUPING', 'SUBTITLE', 'DISCSUBTITLE', 'TRACKNUMBER', 'TRACKTOTAL and    TOTALTRACKS', 'DISCNUMBER', 'DISCTOTAL and TOTALDISCS', 'COMPILATION', 'COMMENT', 'COMMENTS', 'GENRE', 'BPM', 'MOOD', 'ISRC', 'COPYRIGHT', 'LYRICS', 'MEDIA', 'LABEL', 'CATALOGNUMBER', 'BARCODE', 'ENCODEDBY', 'ENCODERSETTINGS', 'ALBUMSORT', 'ALBUMARTISTSORT', 'ARTISTSORT', 'TITLESORT', 'COMPOSERSORT', '', 'ASIN', '', '', '', '', 'SCRIPT', 'LANGUAGE', 'LICENSE', 'ORIGINALYEAR', 'ACOUSTID_ID', 'ACOUSTID_FINGERPRINT', 'WEBSITE', 'WORK', '', '', '', ''
            ],
            'APEv2': [
                'Album', 'Title', 'Artist', 'Album Artist', 'Year', 'Year', '', 'Composer', 'Lyricist', 'Writer', 'Conductor', 'Performerinstrument', 'MixArtist', 'Arranger', 'Engineer', 'Producer', 'DJMixer', 'Mixer', 'Grouping', 'Subtitle', 'DiscSubtitle', 'Track', 'Track', 'Disc', 'Disc', 'Compilation', 'Comment', 'Comments', 'Genre', 'BPM', 'Mood', 'ISRC', 'Copyright', 'Lyrics', 'Media', 'Label', 'CatalogNumber', 'Barcode', 'EncodedBy', 'EncoderSettings', 'ALBUMSORT', 'ALBUMARTISTSORT', 'ARTISTSORT', 'TITLESORT', 'COMPOSERSORT', '', 'ASIN', '', '', '', '', 'Script', 'Language', 'LICENSE', 'ORIGINALYEAR', 'ACOUSTID_ID', 'ACOUSTID_FINGERPRINT', 'Weblink', 'WORK', '', '', '', ''
            ],
        }

        self.tags_db['common'] = self.tags_common
        # Full list of all the aforementioned, for lookup.
        self.tags_all = {}
        for type in self.tags_db:
            for n in range(len(self.tags_db[type])):
                # If these are iTunes tags, ignore the colons.
                # Otherwise, save only the part before the colon.
                item = self.tags_db[type][n]
                if not 'iTunes' in item:
                    item = item.split(':')[0]
                self.tags_all[item] = n

        # Human-readable versions of the tags. These are shown when adding
        # a list of tags to the video's description.
        self.tags_readable = [
            'Album', 'Title', 'Artist', 'Album Artist', 'Release Date', 'Release Date', 'Original Release Date', 'Composer', 'Lyricist', 'Writer', 'Conductor', 'Performer', 'Remixer', 'Arranger', 'Engineer', 'Producer', 'Mix-DJ', 'Mixer', 'Grouping', 'Subtitle', 'Disc Subtitle', 'Track Number', 'Total Tracks', 'Disc Number', 'Total Discs', 'Compilation (iTunes)', 'Comment', 'Comment', 'Genre', 'BPM', 'Mood', 'ISRC', 'Copyright', 'Lyrics', 'Media', 'Record Label', 'Catalog Number', 'Barcode', 'Encoded By', 'Encoder Settings', 'Album Sort Order', 'Album Artist Sort Order', 'Artist Sort Order', 'Title Sort Order', 'Composer Sort Order', 'Show Name Sort Order', 'ASIN', 'Gapless Playback', 'Podcast', 'Podcast URL', 'Show Name', 'Script', 'Language', 'License', 'Original Year', 'AcoustID', 'AcoustID Fingerprint', 'Website', 'Work Title', 'Website', 'Original Artist', 'Date', 'Track Number'
        ]
        

    # Lookup function that translates any system's tag (e.g. ID3v2's TLAN or 
    # Vorbis's ALBUMARTISTSORT) into a human-readable string.
    def tag_lookup(self, tag, human_readable=False):
        tag_key = tag.split(':')[0]
        try:
            tag_code = self.tags_all[tag_key] % len(self.tags_readable)
            if human_readable:
                return self.tags_readable[tag_code]
            else:
                return self.tags_common[tag_code]
        except:
            return tag


class Tune2Tube(object):
    def __init__(self):
        self.settings = {
            # ffmpeg is a dependency for this script. ffprobe should be
            # installed along with ffmpeg.
            'path_ffmpeg': 'ffmpeg',
            'path_ffprobe': 'ffprobe',
            # Temporary output filename.
            'path_output': 'tmp.mp4',
            # Version--todo: change to commit number
            't2t_version': '0.1',
            # Whether to display ffmpeg/ffprobe output.
            'verbose': False,
            # Whether to only generate the video file without uploading it.
            'generate_only': False,
            # Whether to forego the usage of stored oauth2 tokens.
            # If set to True, you will need to authenticate using your
            # browser each time you use the script.
            'no_stored_auth': False,
            # Default title to use in case the user's own title is
            # an empty string.
            'default_title': '(Empty title)',
            # Default variables to use for the dynamically generated title.
            'default_title_vars': 'artist,title',
            # Whether to use the dynamically generated title
            # from the file's metadata.
            'dynamic_title': True,
            'title': None,
            'title_vars': None
        }
    
        # Explicitly tell the underlying HTTP transport library not to retry,
        # since we are handling retry logic ourselves.
        httplib2.RETRIES = 1

        # Maximum number of times to retry before giving up.
        self.max_retries = 10

        # Always retry when these exceptions are raised.
        self.retriable_exceptions = (
            httplib2.HttpLib2Error, IOError, httplib.NotConnected,
            httplib.IncompleteRead, httplib.ImproperConnectionState,
            httplib.CannotSendRequest, httplib.CannotSendHeader,
            httplib.ResponseNotReady, httplib.BadStatusLine
        )
  
        # Always retry when an apiclient.errors.HttpError with one of these status
        # codes is raised.
        self.retriable_status_codes = [500, 502, 503, 504]

        # This OAuth 2.0 access scope allows an application to upload files to the
        # authenticated user's YouTube channel, but doesn't allow other types of access.
        self.youtube_upload_scope = 'https://www.googleapis.com/auth/youtube.upload'
        self.youtube_api_service_name = 'youtube'
        self.youtube_api_version = 'v3'

        # We can set our uploaded video to one of these statuses.
        self.valid_privacy_statuses = ('public', 'private', 'unlisted')

        # This variable defines a message to display if
        # the client_secrets_file is missing.
        self.missing_client_secrets_message = '''
%s: Error: Please configure OAuth 2.0.

To make this script run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console, which can be accessed
through <https://console.developers.google.com/>. See the README.md file
for more details.
'''
        
        # Set up our command line argument parser.
        # The argparser is initialized in oauth2client/tools.py. We're just
        # adding our own arguments to the ones already defined there.
        argparser.description = 'Generates a video from an image and audio file and uploads it to Youtube.'
        argparser.epilog = 'A Youtube Data API client key is required to use this script, as well as ffmpeg. For help on setting up these dependencies, see this project\'s Github page <http://github.com/msikma/tune2tube/> or the included README.md file.'
        argparser.add_help = True
        # Manually add a help argument, as it is turned off in oauth2client/tools.py.
        argparser.add_argument('--no_stored_auth', action='store_true', help='Forego using stored oauth2 tokens.')
        argparser.add_argument('audio_file', help='Audio file (MP3, OGG, FLAC, etc).')
        argparser.add_argument('image_file', help='Image file (PNG, JPG, etc).')
        argparser.add_argument('--output', help='Save the output video (.MP4) to a file rather than uploading it to Youtube.')
        argparser.add_argument('--cs_json', help='Path to the client secrets json file (default: client_secrets.json).', default='client_secrets.json')
        argparser.add_argument('--privacy', choices=self.valid_privacy_statuses, help='Privacy status of the video (default: unlisted).', default='unlisted')
        argparser.add_argument('--category', default='10', help='Numeric video category (see the Github wiki for a list; the default is 10, Music).')
        argparser.add_argument('--keywords', help='Comma-separated list of video keywords/tags.', default='')
        mxgroup = argparser.add_mutually_exclusive_group()
        mxgroup.add_argument('--title', help='Video title string (default: \'%s\'). If neither --title nor --title_vars is specified, --title_vars will be used with its default value, unless this would result in an empty title.' % self.settings['default_title'])
        mxgroup.add_argument('--title_vars', nargs='?', help='Comma-separated list of metadata variables to use as the video title (default: %s).' % self.settings['default_title_vars'])
        argparser.add_argument('--title_sep', help='Separator for the title variables (default: \' - \', yielding e.g. \'Artist - Title\'). Ignored if using --title_str.', default=' - ')
        argparser.add_argument('--description', nargs='?', help='Video description string (default: empty string).', default='')
        argparser.add_argument('--add_metadata', action='store_true', help='Adds a list of audio file metadata to the description (default: True).', default=True)
        argparser.add_argument('-V', '--version', action='version', version='%(prog)s '+self.settings['t2t_version'], help='Show version number and exit.')
        mxgroup = argparser.add_mutually_exclusive_group()
        mxgroup.add_argument('-v', '--verbose', action='store_true', help='Verbose mode (display ffmpeg/ffprobe output).')
        mxgroup.add_argument('-q', '--quiet', action='store_true', help='Quiet mode.')
        argparser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit.')
        
        self.tunetags = TuneTags()
        

    # Get authenticated and cache the result.
    def get_authenticated_service(self, args):
        flow = flow_from_clientsecrets(
            self.settings['client_secrets_file'],
            scope = self.youtube_upload_scope,
            message = self.missing_client_secrets_message % (this_file, os.path.abspath(os.path.join(os.path.dirname(__file__), self.settings['client_secrets_file'])))
        )
    
        storage = Storage('%s-oauth2.json' % this_file)
        credentials = storage.get()
        if credentials is None or credentials.invalid or self.settings['no_stored_auth']:
            credentials = run_flow(flow, storage, args)
    
        return build(
            self.youtube_api_service_name,
            self.youtube_api_version,
            http = credentials.authorize(httplib2.Http())
        )


    # Begin a resumable video upload.
    def initialize_upload(self, youtube, args, file):
        tags = None
    
        if self.settings['keywords']:
            tags = self.settings['keywords'].split(',')
    
        # If we need to generate a dynamic title, do so now.
        if self.settings['dynamic_title']:
            title_vars = self.settings['title_vars'].split(',')
            items = [self.settings['metadata'][n] for n in title_vars if n in self.settings['metadata']]
            title = self.settings['title_sep'].join(items)
        else:
            title = self.settings['title']
    
        # Add the metadata tags to the description if needed.
        description = self.settings['description'].strip()
        if self.settings['add_metadata']:
            if description is not '':
                description = description+'\n'
            # Sort the list of metadata, so that items with linebreaks go last.
            metalist = [{key: self.settings['metadata'][key]} for key in self.settings['metadata']]
            metalist = sorted(metalist, key=lambda x: '\n' in list(x.values())[0])
            for tag in metalist:
                for key in tag:
                    value = tag[key]
                    nice_key = self.tunetags.tag_lookup(key, True)
                    if '\n' in value:
                        description += '\n----\n%s: %s\n' % (nice_key, value)
                    else:
                        description += '\n%s: %s' % (nice_key, value)
    
        body = dict(
            snippet = dict(
                title = title,
                description = description,
                tags = tags,
                categoryId = self.settings['category']
            ),
            status = dict(
                privacyStatus = self.settings['privacy']
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
        self.resumable_upload(insert_request)


    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    def resumable_upload(self, insert_request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if 'id' in response:
                    print("Video ID `%s' was successfully uploaded. Its visibility is set to `%s'." % (response['id'], self.settings['privacy']))
                    print('URL of the newly uploaded video: <https://www.youtube.com/watch?v=%s>' % response['id'])
                    print('It may take some time for the video to finish processing; typically 1-10 minutes.')
                else:
                    error_exit('The upload failed with an unexpected response: %s' % response)
            except HttpError, e:
                if e.resp.status in self.retriable_status_codes:
                    error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
                else:
                    raise
            except self.retriable_exceptions, e:
                error = 'A retriable error occurred: %s' % e
            
            if error is not None:
                print(error)
                retry += 1
                if retry > max_retries:
                    error_exit('Too many upload errors. No longer attempting to retry.')
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print('Sleeping %f seconds and then retrying...' % sleep_seconds)
                time.sleep(sleep_seconds)
    
    
    def generate_video(self, audio, image):
        # Check to see if our files exist at all.
        if not (os.path.exists(audio) and os.path.exists(image)):
            error_exit('please specify a valid audio and image file')
    
        in_image_ext = os.path.splitext(image)[1];
        in_audio_ext = os.path.splitext(audio)[1];
    
        # Check our MP3/OGG/FLAC/etc file and get its duration.
        probe_cmd = [self.settings['path_ffprobe'], audio];
        try:
            probe_out = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
            if self.settings['verbose']:
                print(probe_out)
        except:
            error_exit("couldn't probe the audio file (ffprobe might not be available)")
    
        # Try to extract some metadata from the file using Mutagen.
        try:
            metadata = mutagen.File(audio)
        except AttributeError:
            metadata = []
    
        # Save a human-readable version of the metadata in the object.
        # Keep the original Mutagen output around too.
        self.settings['metadata'] = {}
        self.settings['orig_metadata'] = metadata
        for tag in metadata:
            item = metadata[tag]
            # We join the item in case it's still a list, as in the case
            # of Vorbis.
            if isinstance(item, (list, tuple)):
                item = ''.join(item)
            self.settings['metadata'][self.tunetags.tag_lookup(tag)] = str(item)
    
        # Lift the actual track duration string out of the output.
        duration = re.findall('Duration: (.+?),', probe_out)

        # If we get valid output, parse the duration and get a seconds value.
        # Otherwise, stop the script.
        if len(duration):
            duration = duration[0]
        else:
            error_exit("couldn't parse ffprobe's output. Try again with -v (--verbose) to see what went wrong.")

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
            error_exit('encountered an error trying to determine the duration of the audio file. It could be in an unrecognized format, or longer than 24 hours. (Duration: %s, exception: %s)' % (duration, sys.exc_info()[0]))

        print('Using image file `%s\', size: %s.' % (image, os.path.getsize(image)))
        print('Using audio file `%s\', size: %s, duration: %s.' % (audio, os.path.getsize(audio), duration))
    
        if self.settings['metadata'] == []:
            print("Couldn't extract audio file tags. Continuing.")
        else:
            print('Extracted %d tag(s) from the audio file.' % len(self.settings['metadata']))
    
        print('Encoding video file...')
    
        # Now call ffmpeg and produce the video.
        ffmpeg_cmd = [self.settings['path_ffmpeg'],
            # loop the video (picture) for the movie's duration
            '-loop', '1',
            # a framerate of 1fps (anything lower won't be accepted by Youtube)
            '-framerate', '1:1',
            # one input file is the picture
            '-i', image,
            # automatically overwrite on duplicate
            '-y',
        ]
        # Add the audio file.
        if in_audio_ext == '.flac':
            # mp4 doesn't take flac very well, so we'll convert it.
            ffmpeg_cmd.extend([
                # one input file is the audio
                '-i', audio,
                # for compatibility with various builds, we'll use MP3
                '-c:a', 'libmp3lame',
                # high quality CBR is good enough
                '-b:a', '320k',
            ])
        else:
            ffmpeg_cmd.extend([
                # one input file is the audio
                '-i', audio,
                # only copy the audio, don't re-encode it
                '-c:a', 'copy',
            ])
        # Add the video encoding options.
        ffmpeg_cmd.extend([
            # use x264 as the video encoder
            '-c:v', 'libx264',
            # duration of the video
            '-t', str(delta.total_seconds()),
            # 4:4:4 chroma subsampling (best quality)
            '-pix_fmt', 'yuv444p',
            # as fast as possible, at cost of filesize (uploading costs less time)
            '-preset', 'ultrafast',
            # lossless quality
            '-qp', '0',
            # output
            self.settings['path_output']
        ])
    
        try:
            probe_out = subprocess.check_output(ffmpeg_cmd, stderr=subprocess.STDOUT)
            if self.settings['verbose']:
                print(probe_out)
        except:
            error_exit('encountered an error trying to generate the video. Try again with -v (--verbose) to see what went wrong. (Exception: %s)' % sys.exc_info()[0])
    
        print('Successfully generated the file `%s\'.' % self.settings['path_output'])


    def upload_tune(self, audio, image, video_ready=False):
        if not video_ready:
            self.generate_video(audio, image)
    
        if self.settings['generate_only']:
            print('Skipping Youtube upload.')
            exit()
    
        # Now upload the file to Youtube.
        print('Authenticating using the Youtube API...')
        try:
            youtube = self.get_authenticated_service(args)
        except httplib2.ServerNotFoundError, e:
            error_exit('%s.' % e)
    
        try:
            self.initialize_upload(youtube, args, self.settings['path_output'])
        except HttpError, e:
            print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
        except AccessTokenRefreshError, e:
            print('The stored access token seems to be invalid. Delete any -oauth2.json files that may exist and try again, or try again with the --no_stored_auth switch.')
    
    
    def change_settings(self, overrides):
        self.settings = dict(self.settings.items() + overrides.items())


if __name__ == '__main__':
    # Run the script using our command line arguments.
    t2t = Tune2Tube()
    
    # Check to ensure we've got valid command line arguments.
    args = argparser.parse_args()

    # From here we can assume we have our required arguments.
    in_image = args.image_file
    in_audio = args.audio_file

   # Decide whether to go with the standard title or the metadata title.
    if args.title is None and args.title_vars is None:
        args.dynamic_title = True
        args.title_vars = t2t.settings['default_title_vars']
    if args.title_vars is not None:
        args.dynamic_title = True
    if args.title_vars is None:
        args.title_vars = ''
    if args.description is None:
        args.description = ''
    if args.cs_json:
        args.client_secrets_file = args.cs_json
    if args.output:
        args.generate_only = True
        args.path_output = args.output
    
    # Stick our command line arguments into the class.
    t2t.change_settings(vars(args))

    # Upload each tune that's been queued.
    tunes = [{'audio': in_audio, 'image': in_image}]
    for tune in tunes:
        t2t.upload_tune(tune['audio'], tune['image'])
