#!/usr/bin/env python3

import datetime
import sys
import time
import threefive
from threefive import Cue
from iframes import IFramer
from m3ufu import M3uFu, TagParser, HEADER_TAGS
from new_reader import reader

REV = "\033[7m"
NORM = "\033[27m"


def atoif(value):
    """
    atoif converts ascii to (int|float)
    """
    if "." in value:
        try:
            value = float(value)
        finally:
            return value
    else:
        try:
            value = int(value)
        finally:
            return value


def iso8601():
    """
    return UTC time in iso8601 format.

    '2023-05-11T15:55:51.'

    """
    return f"{datetime.datetime.utcnow().isoformat().split('.')[0]}"


class Pane:
    """
    Pane class. Sliding_Window slides Panes
    """

    def __init__(self, media, lines):
        self.media = media
        self.lines = lines

    def get(self):
        all_lines = self.lines + [self.media]
        return "".join(all_lines)


class SlidingWindow:
    """
    The Sliding Window class
    """

    def __init__(self, size=10000):
        self.size = size
        self.panes = []
        self.delete = False

    def pop_pane(self):
        """
        pop_pane removes the first item in self.panes
        """
        if len(self.panes) >= self.size:
            # popped = self.panes[0].media
            self.panes = self.panes[1:]

    def push_pane(self, a_pane):
        """
        push appends a_pane to self.panes
        """
        self.panes.append(a_pane)

    def all_panes(self):
        """
        all_panes returns the current window panes joined.
        """
        return "".join([a_pane.get() for a_pane in self.panes])

    def slide_panes(self, a_pane):
        """
        slide calls self.push_pane with a_pane
        and then calls self.pop_pane to trim self.panes
        as needed.
        """
        self.push_pane(a_pane)
        self.pop_pane()


class CuePuller:
    MEDIA_COUNT = 111

    def __init__(self):
        self.cues = []
        self.media = []
        self.media_count = 101
        self.sidecar_file = "cp_sidecar.txt"
        self.base_uri = None
        self.iv = None
        self.key_uri = None
        self.last_iv = None
        self.last_key_uri = None
        self.event_id = 1
        self.break_timer = None
        self.break_duration = None
        self.m3u8 = "cp.m3u8"
        self.lines = []
        self.reload = True
        self.sleep_duration = 0
        self.window_size = None
        self.sliding_window = None
        self.cue_state = None
        self.last_cue = None
        self.headers = []
        self.pts = None
        self.hls_pts = "HLS"

    def chk_aes(self, line):
        """
        chk_aes checks for AES encryption
        """
        if "#EXT-X-KEY" in line:
            tags = TagParser([line]).tags
            if "URI" in tags["#EXT-X-KEY"]:
                self.key_uri = tags["#EXT-X-KEY"]["URI"]
                if not self.key_uri.startswith("http"):
                    re_uri = self.base_uri + self.key_uri
                    self.key_uri = re_uri
                if "IV" in tags["#EXT-X-KEY"]:
                    self.iv = tags["#EXT-X-KEY"]["IV"]

    def six2five(self, cuein):
        """
        six2five converts Time Signals (type 6)
        to SpliceInserts (type 5)
        """
        upid_starts = [0x34, 0x36, 0x38]
        upid_stops = [0x35, 0x37, 0x39]
        cue = threefive.Cue(cuein)
        cue.decode()
        if cue.command.command_type == 5:
            return cue.encode()
        pts = None
        duration = None
        out = False
        event_id = self.event_id
        if cue.command.pts_time:
            pts = cue.command.pts_time
        for dscptr in cue.descriptors:
            if dscptr.tag == 2:
                if dscptr.segmentation_event_id:
                    event_id = int(dscptr.segmentation_event_id, 16) & (2 ^ 31)
                    if dscptr.segmentation_type_id in upid_starts:
                        if dscptr.segmentation_duration_flag:
                            duration = dscptr.segmentation_duration
                            out = True
                    else:
                        if dscptr.segmentation_type_id in upid_stops:
                            out = False
        new_cue = threefive.encode.mk_splice_insert(event_id, pts, duration, out)
        new_cue.descriptors = cue.descriptors
        cue = new_cue
        if cue.command.splice_immediate_flag:
            print("Splice Immediate")
        if cue.command.out_of_network_indicator:
            if self.break_timer is None:
                self.break_timer = 0.0
        if cue.command.break_duration:
            self.break_duration = cue.command.break_duration
        return cue.encode()

    def add_cue(self, cue, line):
        """
        add_cue determines cue_state and
        calls six2five to replace time signals
        """
        cue = cue.replace("\r", "").replace("\n", "")
        if "CONT" not in line:
            cue_stuff = f"{REV}{self.cue_state}{NORM} {cue} "
            media_stuff = f"\n{REV}Media:{NORM} {self.media[-1]}\n"
            if cue == "#EXT-X-CUE-IN":
                self.cue_state = "IN"
                diff_stuff = f" {REV}Diff:{NORM} {round(self.break_timer - self.break_duration,3)}"
                print(f"{iso8601()} {cue_stuff} {diff_stuff}{media_stuff}")
                self.reset_break()
                return line
            if cue.startswith("#EXT-X-CUE-OUT"):
                self.break_timer == 0.0
                try:
                    self.break_duration = atoif(line.split(":")[1])
                finally:
                    self.cue_state = "OUT"
                print(f"{iso8601()} {cue_stuff} {REV}Duration:{NORM} {self.break_duration} {media_stuff}")
                return line
        cue2 = self.six2five(cue)
        cue2data = Cue(cue2)
        cue2data.decode()
        line = line.replace(cue, cue2)
        return line

    def chk_x_cue_out_cont(self, tags, line):
        """
        chk_x_cue_out_const processes
        #EXT-X-CUE-OUT-CONT tags
        """
        cont_tags = tags["#EXT-X-CUE-OUT-CONT"]
        if self.cue_state in ["OUT", "CONT"]:
            self.cue_state = "CONT"
            if self.cue_state == "OUT" and self.break_timer is None:
                if "ElapsedTime" in cont_tags:
                    self.break_timer = cont_tags["ElapsedTime"]
                    print("setting break timer to ", cont_tags["ElapsedTime"])

                if "Duration" in cont_tags:
                    self.break_duration = cont_tags["Duration"]
            return line
        return "## " + line

    def chk_x_cue_in(self, line):
        if self.cue_state == "CONT":
            if self.break_timer is not None:
                self.cue_state = "IN"
                val = self.add_cue(line, line)
                self.reset_break()
                return val
        return "## " + line

    def chk_x_cue_out(self, line):
        """
        chk_x_cue_out processes
        #EXT-X-CUE-OUT tags
        """
        if self.cue_state is None:
            self.reset_break()
            self.cue_state = "OUT"
            if self.break_timer is None:
                self.break_timer = 0.0
            if ":" in line:
                self.break_duration = atoif(line.split(":")[1])
               # print("Duration:", self.break_duration)
            return self.add_cue(line, line)
        return "## " + line

    def chk_x_scte35(self, tags, line):
        if "CUE" in tags["#EXT-X-SCTE35"]:
            return self.add_cue(tags["#EXT-X-SCTE35"]["CUE"], line)
        return line

    def chk_x_daterange(self, tags, line):
        for scte35_tag in ["SCTE35-OUT", "SCTE35-IN"]:
            if scte35_tag in tags["#EXT-X-DATERANGE"]:
                return self.add_cue(tags["#EXT-X-DATERANGE"][scte35_tag], line)
        return line

    def scte35(self, line):
        """
        scte35 processes SCTE-35 related tags.
        """
        tags = TagParser([line]).tags
        if "#EXT-X-SCTE35" in tags:
            return self.chk_x_scte35(tags, line)
        if "#EXT-X-CUE-OUT-CONT" in tags:
            return self.chk_x_cue_out_cont(tags, line)
        if "#EXT-X-DATERANGE" in tags:
            return self.chk_x_daterange(tags, line)
        if "#EXT-OATCLS-SCTE35" in tags:
            return self.add_cue(tags["#EXT-OATCLS-SCTE35"], line)
        if "#EXT-X-CUE-IN" in line:
            return self.chk_x_cue_in(line)
        if "#EXT-X-CUE-OUT" in line:
            return self.chk_x_cue_out(line)
        return line

    def auto_cuein(self, line):
        """
        auto_cuein handles cue.command.autoreturn
        """
        if self.cue_state == "CONT":
            if self.break_timer and self.break_duration:
                if self.break_timer >= self.break_duration:
                    self.cue_state = "IN"
                    print(
                        f"{iso8601()} {REV}AUTO{NORM} #EXT-X-CUE-IN{REV}Diff:{NORM}{round(self.break_timer - self.break_duration,3)} \n{REV}Media:{NORM} {self.media[-1]}\n"
                    )
                    self.reset_break()
                    return "\n#AUTO\n#EXT-X-CUE-IN\n" + line
        return line

    def reset_break(self):
        """
        reset_break resets
        break_duration, break_timer,
        and cue_state after a CUE-IN
        """
        if self.cue_state == "IN":
            self.break_duration = None
            self.break_timer = None
            self.cue_state = None

    def extinf(self, line):
        """
        extinf parses lines that start with #EXTINF
        for the segment duration.
        """
        tags = TagParser([line]).tags
        if "#EXTINF" in tags:
            if isinstance(tags["#EXTINF"], str):
                tags["#EXTINF"] = tags["#EXTINF"].rsplit(",", 1)[0]
            seg_time = round(float(tags["#EXTINF"]), 6)
            line = self.auto_cuein(line)
            if self.pts is not None:
                self.pts += seg_time
            if self.break_timer is not None:
                self.break_timer += seg_time
        return line

    def new_media(self, media):
        """
        new_media check to see
        if the media is new in a
        live sliding window
        """
        if media not in self.media:
            self.media.append(media)
            if self.pts is None:
                media = media.replace("\n", "")
                if ".ts" in media:
                    Iframer = IFramer(shush=True)
                    iframes = Iframer.do(media)
                    self.pts = iframes[0]
                    self.hls_pts = "PTS"
                else:
                    self.pts = 0
            # print(f"Starting {self.hls_pts} Time:{ self.pts}\n")
            self.media = self.media[-self.window_size * 2 :]
            return True
        return False

    def parse_target_duration(self, line):
        if line.startswith("#EXT-X-TARGETDURATION"):
            self.sleep_duration = round((atoif(line.split(":")[1]) >> 1), 3)

    def mk_window_size(self, lines):
        if not self.window_size:
            self.window_size = len(
                [line for line in lines if line.startswith("#EXTINF:")]
            )
            self.sliding_window.size = self.window_size
            print(f"{REV}Window_size:{NORM} {self.window_size}\n")

    def update_cue_state(self):
        if self.cue_state == "OUT":
            self.cue_state = "CONT"
        if self.cue_state == "IN":
            self.cue_state = None

    @staticmethod
    def decode_lines(lines):
        return [line.decode() for line in lines]

    def parse_line(self, line):
        if line.startswith("#EXTINF:"):
            line = self.extinf(line)
            return line
        self.parse_target_duration(line)
        self.chk_aes(line)
        line = self.scte35(line)
        return line

    def parse_header(self, line):
        splitline = line.split(":", 1)
        if splitline[0] in HEADER_TAGS:
            self.headers.append(line)
            return True
        return False

    def pull(self, manifest):
        print(f"{REV}Started{NORM}\n")
        print(f"\n{REV}variant m3u8:{NORM} {manifest}\n")
        self.base_uri = manifest.rsplit("/", 1)[0]
        self.sliding_window = SlidingWindow()
        while self.reload:
            lines = []
            self.headers = []
            with reader(manifest) as m3u8:
                m3u8_lines = self.decode_lines(m3u8.readlines())
                self.mk_window_size(m3u8_lines)
                for line in m3u8_lines:
                    if "#EXT-X-ENDLIST" in line:
                        self.reload = False
                    if line.startswith("#"):
                        if not self.parse_header(line):
                            lines.append(line)
                    if not line.startswith("#"):
                        media = line
                        if not media.startswith("http"):
                            media = self.base_uri + "/" + media
                        if self.new_media(media):
                            lines = [self.parse_line(line) for line in lines]
                            pane = Pane(media, lines)
                            self.sliding_window.slide_panes(pane)
                        lines = []
            ##            with open(self.m3u8, "w") as out:
            ##                out.write("#EXTM3U\n")
            ##                out.write("".join(self.headers))
            ##                out.write(self.sliding_window.all_panes())
            self.update_cue_state()
            time.sleep(self.sleep_duration)


def cli():
    playlists=None
    m3u8 = None
    with reader(sys.argv[1]) as arg:
        variants = [line for line in arg if b"#EXT-X-STREAM-INF" in line]
        if variants:
            fu = M3uFu()
            reload =False
            fu.m3u8 = sys.argv[1]
            fu.decode()
            playlists = [
                segment for segment in fu.segments if "#EXT-X-STREAM-INF" in segment.tags
            ]
    if playlists:
        m3u8 = playlists[0].media
    else:
        m3u8 = sys.argv[1]
    cp = CuePuller()
    cp.pull(m3u8)




if __name__ == "__main__":
    cli()
