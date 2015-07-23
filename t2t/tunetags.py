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


class TuneTags(object):
    '''
    Used to look up and normalize tags in audio files.
    Contains a dict with tag key names for various file formats.
    The keys are linked to a list of human-readable labels.
    '''

    def __init__(self):
        # A list of MP3/OGG/ASF/MP4/APE tags that we might encounter.
        self.tags_common = [
            'album', 'title', 'artist', 'album-artist', 'release-date',
            'release-date', 'original-release-date', 'composer', 'lyricist',
            'writer', 'conductor', 'performer', 'remixer', 'arranger',
            'engineer', 'producer', 'mix-dj', 'mixer', 'grouping', 'subtitle',
            'disc-subtitle', 'track-number', 'total-tracks', 'disc-number',
            'total-discs', 'compilation-itunes', 'comment', 'comments',
            'genre', 'bpm', 'mood', 'isrc', 'copyright', 'lyrics', 'media',
            'record-label', 'catalog-number', 'barcode', 'encoded-by',
            'encoder-settings', 'album-sort-order', 'album-artist-sort-order',
            'artist-sort-order', 'title-sort-order', 'composer-sort-order',
            'show-name-sort-order', 'asin', 'gapless-playback', 'podcast',
            'podcast-url', 'show-name', 'script', 'language', 'license',
            'original-year', 'acoustid', 'acoustid-fingerprint', 'website',
            'work-title', 'website', 'original-artist', 'date', 'tracknumber'
        ]
        self.tags_db = {
            'ID3v23': [
                'TALB', 'TIT2', 'TPE1', 'TPE2', 'TYER', 'TDAT', 'TORY', 'TCOM',
                'TEXT', 'TXXX:Writer', 'TPE3', 'IPLS:instrument', 'TPE4',
                'IPLS:arranger', 'IPLS:engineer', 'IPLS:producer',
                'IPLS:DJ-mix', 'IPLS:mix', 'TIT1', 'TIT3', '', 'TRCK', 'TRCK',
                'TPOS', 'TPOS', 'TCMP', 'COMM:description', 'TCON', 'TBPM', '',
                'TSRC', 'TCOP', 'USLT:description', 'TMED', 'TPUB',
                'TXXX:CATALOGNUMBER', 'TXXX:BARCODE', 'TENC', 'TSSE', 'TSOA',
                'TSO2', 'TSOP', 'TSOT', 'TSOC', '', 'TXXX:ASIN', '', '', '',
                '', 'TXXX:SCRIPT', 'TLAN', 'WCOPTXXX:LICENSE',
                'TXXX:originalyear', 'TXXX:Acoustid Id',
                'TXXX:Acoustid Fingerprint', 'WOAR', 'TOAL', 'WXXX:website',
                'TOPE', '', ''
            ],
            'ID3v24': [
                'TALB', 'TIT2', 'TPE1', 'TPE2', 'TDRC', 'TDRC', 'TDOR', 'TCOM',
                'TEXT', 'TXXX:Writer', 'TPE3', 'TMCL:instrument', 'TPE4',
                'TIPL:arranger', 'TIPL:engineer', 'TIPL:producer',
                'TIPL:DJ-mix', 'TIPL:mix', 'TIT1', 'TIT3', 'TSST', 'TRCK',
                'TRCK', 'TPOS', 'TPOS', 'TCMP', 'COMM:description', 'TCON',
                'TBPM', 'TMOO', 'TSRC', 'TCOP', 'USLT:description', 'TMED',
                'TPUB', 'TXXX:CATALOGNUMBER', 'TXXX:BARCODE', 'TENC', 'TSSE',
                'TSOA', 'TXXX:ALBUMARTISTSORT', 'TSOP', 'TSOT',
                'TXXX:COMPOSERSORT', '', 'TXXX:ASIN', '', '', '', '',
                'TXXX:SCRIPT', 'TLAN', 'WCOPTXXX:LICENSE', 'TXXX:originalyear',
                'TXXX:Acoustid Id', 'TXXX:Acoustid Fingerprint', 'WOAR',
                'TOAL', 'WXXX:website', 'TOPE', '', ''
            ],
            'ASF/Windows Media': [
                'WM/AlbumTitle', 'Title', 'Author', 'WM/AlbumArtist',
                'WM/Year', 'WM/Year', 'WM/OriginalReleaseYear', 'WM/Composer',
                'WM/Writer', '', 'WM/Conductor', '', 'WM/ModifiedBy', '',
                'WM/Engineer', 'WM/Producer', 'WM/DJMixer', 'WM/Mixer',
                'WM/ContentGroupDescription', 'WM/SubTitle', 'WM/SetSubTitle',
                'WM/TrackNumber', '', 'WM/PartOfSet', '', 'WM/IsCompilation',
                'Description', 'WM/Genre', 'WM/BeatsPerMinute', 'WM/Mood',
                'WM/ISRC', 'Copyright', 'WM/Lyrics', 'WM/Media',
                'WM/Publisher', 'WM/CatalogNo', 'WM/Barcode', 'WM/EncodedBy',
                'WM/EncoderSettings', 'WM/AlbumSortOrder',
                'WM/AlbumArtistSortOrder', 'WM/ArtistSortOrder',
                'WM/TitleSortOrder', 'WM/ComposerSortOrder', '', '', '', '',
                '', '', 'WM/Script', 'WM/Language', 'LICENSE', '',
                'Acoustid/Id', 'Acoustid/Fingerprint', '', '', '', '', '', ''
            ],
            'iTunes MP4': [
                '©alb', '©nam', '©ART', 'aART', '©day', '©day', '', '©wrt',
                '----:com.apple.iTunes:LYRICIST', '',
                '----:com.apple.iTunes:CONDUCTOR', '',
                '----:com.apple.iTunes:REMIXER', '',
                '----:com.apple.iTunes:ENGINEER',
                '----:com.apple.iTunes:PRODUCER',
                '----:com.apple.iTunes:DJMIXER', '----:com.apple.iTunes:MIXER',
                '©grp', '----:com.apple.iTunes:SUBTITLE',
                '----:com.apple.iTunes:DISCSUBTITLE', 'trkn', 'trkn', 'disk',
                'disk', 'cpil', '©cmt', '©gen', 'tmpo',
                '----:com.apple.iTunes:MOOD', '----:com.apple.iTunes:ISRC',
                'cprt', '©lyr', '----:com.apple.iTunes:MEDIA',
                '----:com.apple.iTunes:LABEL',
                '----:com.apple.iTunes:CATALOGNUMBER',
                '----:com.apple.iTunes:BARCODE', '©too', '', 'soal', 'soaa',
                'soar', 'sonm', 'soco', 'sosn', '----:com.apple.iTunes:ASIN',
                'pgap', 'pcst', 'purl', 'tvsh', '----:com.apple.iTunes:SCRIPT',
                '----:com.apple.iTunes:LANGUAGE',
                '----:com.apple.iTunes:LICENSE', '',
                '----:com.apple.iTunes:Acoustid Id',
                '----:com.apple.iTunes:Acoustid Fingerprint', '', '', '', '',
                '', ''
            ],
            'Vorbis': [
                'ALBUM', 'TITLE', 'ARTIST', 'ALBUMARTIST', 'DATE', 'DATE',
                'ORIGINALDATE', 'COMPOSER', 'LYRICIST', 'WRITER', 'CONDUCTOR',
                'PERFORMER', 'REMIXER', 'ARRANGER', 'ENGINEER', 'PRODUCER',
                'DJMIXER', 'MIXER', 'GROUPING', 'SUBTITLE', 'DISCSUBTITLE',
                'TRACKNUMBER', 'TRACKTOTAL and    TOTALTRACKS', 'DISCNUMBER',
                'DISCTOTAL and TOTALDISCS', 'COMPILATION', 'COMMENT',
                'COMMENTS', 'GENRE', 'BPM', 'MOOD', 'ISRC', 'COPYRIGHT',
                'LYRICS', 'MEDIA', 'LABEL', 'CATALOGNUMBER', 'BARCODE',
                'ENCODEDBY', 'ENCODERSETTINGS', 'ALBUMSORT', 'ALBUMARTISTSORT',
                'ARTISTSORT', 'TITLESORT', 'COMPOSERSORT', '', 'ASIN', '', '',
                '', '', 'SCRIPT', 'LANGUAGE', 'LICENSE', 'ORIGINALYEAR',
                'ACOUSTID_ID', 'ACOUSTID_FINGERPRINT', 'WEBSITE', 'WORK', '',
                '', '', ''
            ],
            'APEv2': [
                'Album', 'Title', 'Artist', 'Album Artist', 'Year', 'Year', '',
                'Composer', 'Lyricist', 'Writer', 'Conductor',
                'Performerinstrument', 'MixArtist', 'Arranger', 'Engineer',
                'Producer', 'DJMixer', 'Mixer', 'Grouping', 'Subtitle',
                'DiscSubtitle', 'Track', 'Track', 'Disc', 'Disc',
                'Compilation', 'Comment', 'Comments', 'Genre', 'BPM', 'Mood',
                'ISRC', 'Copyright', 'Lyrics', 'Media', 'Label',
                'CatalogNumber', 'Barcode', 'EncodedBy', 'EncoderSettings',
                'ALBUMSORT', 'ALBUMARTISTSORT', 'ARTISTSORT', 'TITLESORT',
                'COMPOSERSORT', '', 'ASIN', '', '', '', '', 'Script',
                'Language', 'LICENSE', 'ORIGINALYEAR', 'ACOUSTID_ID',
                'ACOUSTID_FINGERPRINT', 'Weblink', 'WORK', '', '', '', ''
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
                if 'iTunes' not in item:
                    item = item.split(':')[0]
                self.tags_all[item] = n

        # Human-readable versions of the tags. These are shown when adding
        # a list of tags to the video's description.
        self.tags_readable = [
            'Album', 'Title', 'Artist', 'Album Artist', 'Release Date',
            'Release Date', 'Original Release Date', 'Composer', 'Lyricist',
            'Writer', 'Conductor', 'Performer', 'Remixer', 'Arranger',
            'Engineer', 'Producer', 'Mix-DJ', 'Mixer', 'Grouping', 'Subtitle',
            'Disc Subtitle', 'Track Number', 'Total Tracks', 'Disc Number',
            'Total Discs', 'Compilation (iTunes)', 'Comment', 'Comment',
            'Genre', 'BPM', 'Mood', 'ISRC', 'Copyright', 'Lyrics', 'Media',
            'Record Label', 'Catalog Number', 'Barcode', 'Encoded By',
            'Encoder Settings', 'Album Sort Order', 'Album Artist Sort Order',
            'Artist Sort Order', 'Title Sort Order', 'Composer Sort Order',
            'Show Name Sort Order', 'ASIN', 'Gapless Playback', 'Podcast',
            'Podcast URL', 'Show Name', 'Script', 'Language', 'License',
            'Original Year', 'AcoustID', 'AcoustID Fingerprint', 'Website',
            'Work Title', 'Website', 'Original Artist', 'Date', 'Track Number'
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
        except KeyError:
            return tag
