tune2tube.py
============

This script converts an image and audio file into a movie, and then
uploads that movie to Youtube. It's meant for quickly sharing music.


Synopsis
--------

```
usage: tune2tube.py [--auth_host_name AUTH_HOST_NAME]
                    [--noauth_local_webserver]
                    [--auth_host_port [AUTH_HOST_PORT [AUTH_HOST_PORT ...]]]
                    [--logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [--no_stored_auth] [--output OUTPUT] [--cs_json CS_JSON]
                    [--privacy {public,private,unlisted}]
                    [--category CATEGORY] [--keywords KEYWORDS]
                    [--title TITLE | --title_vars [TITLE_VARS]]
                    [--title_sep TITLE_SEP] [--description [DESCRIPTION]]
                    [--add_metadata] [-V] [-v | -q] [-h]
                    audio_file image_file

Generates a video from an image and audio file and uploads it to Youtube.

positional arguments:
  audio_file            Audio file (MP3, OGG, FLAC, etc).
  image_file            Image file (PNG, JPG, etc).

optional arguments:
  --auth_host_name AUTH_HOST_NAME
                        Hostname when running a local web server.
  --noauth_local_webserver
                        Do not run a local web server.
  --auth_host_port [AUTH_HOST_PORT [AUTH_HOST_PORT ...]]
                        Port web server should listen on.
  --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level of detail.
  --no_stored_auth      Forego using stored oauth2 tokens.
  --output OUTPUT       Save the output video (.MP4) to a file rather than
                        uploading it to Youtube.
  --cs_json CS_JSON     Path to the client secrets json file (default:
                        client_secrets.json).
  --privacy {public,private,unlisted}
                        Privacy status of the video (default: unlisted).
  --category CATEGORY   Numeric video category (see the Github wiki for a
                        list; the default is 10, Music).
  --keywords KEYWORDS   Comma-separated list of video keywords/tags.
  --title TITLE         Video title string (default: '(Empty title)'). If
                        neither --title nor --title_vars is specified,
                        --title_vars will be used with its default value,
                        unless this would result in an empty title.
  --title_vars [TITLE_VARS]
                        Comma-separated list of metadata variables to use as
                        the video title (default: artist,title).
  --title_sep TITLE_SEP
                        Separator for the title variables (default: ' - ',
                        yielding e.g. 'Artist - Title'). Ignored if using
                        --title_str.
  --description [DESCRIPTION]
                        Video description string (default: empty string).
  --add_metadata        Adds a list of audio file metadata to the description
                        (default: True).
  -V, --version         Show version number and exit.
  -v, --verbose         Verbose mode (display ffmpeg/ffprobe output).
  -q, --quiet           Quiet mode.
  -h, --help            Show this help message and exit.

A Youtube Data API client key is required to use this script, as well as
ffmpeg. For help on setting up these dependencies, see this project's Github
page <http://github.com/msikma/tune2tube/> or the included README.md file.
```

Dependencies
------------

Aside from your own Youtube Data API key, you'll need to download a few
libraries [in a virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

You'll need to install [Google's Python API client
library](https://github.com/google/google-api-python-client):

    $ pip install --upgrade google-api-python-client

We'll also need their [OAuth 2.0 client
library](https://github.com/google/oauth2client):

    $ pip install --upgrade oauth2client

(For these two examples, you can use `easy_install` rather than `pip` if
you prefer using that.)

For extracting metadata from various audio files, we use
[Mutagen](https://bitbucket.org/lazka/mutagen/). Download the latest
version, extract it, and run:

    $ ./setup.py build
    $ sudo ./setup.py install


OAuth 2.0 client configuration
------------------------------

To be able to upload files to Youtube, you'll need to set up your own
`client_secrets.json` file containing your OAuth 2.0 keys (for Youtube
API access). Thankfully, Google lets you set up and download such a file
from their [developers console](https://console.developers.google.com/).
To obtain the file, perform the following actions:

1. Once logged in to the [developers
console](https://console.developers.google.com/), you'll need to create
a new project, and then turn on:
1. the **YouTube Analytics API**;
1. and the **YouTube Data API v3**.
1. Then, you need to set up a valid **product name** in the *Consent
Screen* page.
1. Once all that is done, head over to the *Credentials* page and click
the *Download JSON* button.

By default, `tune2tube.py` looks for the `client_secrets.json` file in
its own directory.

If your key seems to be dysfunctional despite all the proper steps
having been taken, you might have hit [a bug in Google's
systems](http://stackoverflow.com/a/23750669/3553425)—try opening the
old console as this user states, and it might fix your problem as it did
for me.


Code style
----------

The code is PEP8-compliant, with the exception of W291 and W293 and
the rules that are ignored by default.


License
-------

Licensed under the [Apache License, Version
2.0](http://opensource.org/licenses/Apache-2.0).
