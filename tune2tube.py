#!/usr/bin/env python
# coding=UTF8

# tune2tube.py
#
# Copyright (C) 2014-2015 Michiel Sikma and contributors
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

import os
from oauth2client.tools import argparser
from t2t import Tune2Tube

this_file = os.path.basename(__file__)

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
        t2t.upload_tune(tune['audio'], tune['image'], args)
