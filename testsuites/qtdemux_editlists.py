# -*- Mode: Python -*- vi:si:et:sw=4:sts=4:ts=4:syntax=python
#
# Copyright (c) 2017,Thibault Saunier <tsaunier@igalia.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA 02110-1301, USA.import textwrap
import textwrap
import tempfile
import os
from launcher.apps.gstvalidate import GstValidateMediaCheckTestsGenerator, GstValidateMediaDescriptor, GstValidateMediaCheckTest

class GstValidateMP4EditListTestGenerator(GstValidateMediaCheckTestsGenerator):
    BASE_XML = textwrap.dedent("""
        <file duration="2000000000" frame-detection="1" uri="file:///medias/defaults/mp4/edit_lists/frag-2-entries-elst_v_0.mp4" seekable="true">
            <streams caps="video/quicktime, variant=(string)iso">
                <!-- Check codec data depending on the input template -->
                <stream type="video" caps="video/x-h264, stream-format=(string)avc, alignment=(string)au, level=(string)1.1, profile=(string)high, codec_data=(buffer)0164000bffe1001d6764000bace40507ec05a830082d280000030008000003003478a1489001000568ebecb22c, width=(int)320, height=(int)240, framerate=(fraction)3/1, pixel-aspect-ratio=(fraction)1/1, colorimetry=(string)bt601, interlace-mode=(string)progressive, chroma-format=(string)4:2:0, bit-depth-luma=(uint)8, bit-depth-chroma=(uint)8, parsed=(boolean)true" id="41a95766e908153ca2e6788fc3e13e9c187a39e28b9867edf40271e6150d5e50/001">
                <segments>
                    %(segments)s
                </segments>
                %(frames)s
                <tags>
                    <tag content="taglist, video-codec=(string)&quot;H.264\ /\ AVC&quot;, maximum-bitrate=(uint)17408, bitrate=(uint)10884, encoder=(string)x264, datetime=(datetime)2018-03-01T17:36:17Z, container-format=(string)&quot;ISO\ fMP4&quot;;"/>
                </tags>
                </stream>
            </streams>
            <tags>
                <tag content="taglist, video-codec=(string)&quot;H.264\ /\ AVC&quot;, maximum-bitrate=(uint)17408, bitrate=(uint)10884, encoder=(string)x264, datetime=(datetime)2018-03-01T17:36:17Z, container-format=(string)&quot;ISO\ fMP4&quot;;"/>
            </tags>
        </file>""")

    class Events():
        def __init__(self):
            self.segments = ""
            self.frames = ""
            self.frame_id = 0

        def frame(self, **args):
            """Requires dts, pts, duration"""

            frame_values = {"id": self.frame_id,
                "is_keyframe": "unknown",
                "offset": "unknown",
                "offset_end": "unknown",
                "running_time": "unknown",
                "checksum": "unknown",
                "dts": "unknown"
            }
            frame_values.update(**args)

            self.frames += textwrap.dedent("""
            <frame duration="%(duration)s"
                id="%(id)s" is-keyframe="%(is_keyframe)s"
                offset="%(offset)s" offset-end="%(offset_end)s" pts="%(pts)s"
                dts="%(dts)s" running-time="%(running_time)s" checksum="%(checksum)s"/>""") % frame_values
            self.frame_id += 1

            return self
        
        def segment(self, start, duration, **args):
            segment_values={"previous_frame_id": self.frame_id,
                "flags": 0, "rate": 1.0, "applied_rate": 1.0, "format": 3, # time
                "offset": 0, "start": start, "duration": "18446744073709551615", # HACK! Fixme.
                "base": start, "time": start, "stop": start + duration, "position": 0
            }

            segment_values.update(**args)
            self.segments += textwrap.dedent("""
            <segment previous_frame_id="%(previous_frame_id)s"
                flags="%(flags)s" rate="%(rate)s" applied-rate="%(applied_rate)s"
                format="%(format)s" base="%(base)s" offset="%(offset)s"
                start="%(start)s" stop="%(stop)s" time="%(time)s"
                position="%(position)s"
                duration="%(duration)s"/>\n""") % segment_values

            return self

    class MediaDesriptor(GstValidateMediaDescriptor):
        def __init__(self, events):
            self.temp_xml_file = tempfile.NamedTemporaryFile(suffix="media_info")
            with open(self.temp_xml_file.name, "w") as xml_file:
                xml_file.write(GstValidateMP4EditListTestGenerator.BASE_XML % events.__dict__)
                print(GstValidateMP4EditListTestGenerator.BASE_XML % events.__dict__)

            super().__init__(self.temp_xml_file.name)

    def __init__(self, test_manager, assets_path):
        self.assets_path = assets_path
        super().__init__(test_manager)

    def populate_tests(self, uri_minfo_special_scenarios, scenarios):
        # Make that a list and do smart stuff here?
        # Patch it up to generate the streams?
        uri = "file://" + os.path.join(self.assets_path, "mp4", "edit_lists", "frag-2-entries-elst_v_0.mp4")
        media_descriptor = self.MediaDesriptor(self.Events()
            .segment(0, 1000000000)
            .segment(333333333, 2000000000, time=1000000000, base=1000000000, position=333333333)
            # FIXME Add stream_tim support on top of running_time.
            .frame(pts=333333333, duration=1)
            .frame(pts=1000000000, duration=333333333)
            .frame(pts=666666666, duration=333333333)
            .frame(pts=1333333333, duration=333333333)
            .frame(pts=2000000000, duration=333333333)
            .frame(pts=1666666666, duration=333333333))

        self.add_test(GstValidateMediaCheckTest("file.qtdemux.edit_lists.frag-2-entries-elst_v_0_mp4",
                                                self.test_manager.options,
                                                self.test_manager.reporter,
                                                media_descriptor,
                                                uri,
                                                media_descriptor.get_path()))
