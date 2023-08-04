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
SUB = "\n\t\t\t "


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
    return f"{REV}{datetime.datetime.utcnow().isoformat()[:-4]}Z{NORM} "


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
        if len(self.panes) > self.size:
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
    def __init__(self):
        self.cues = []
        self.media = []
        self.media_count = 101
        self.sidecar = "sidecar.txt"
        self.base_uri = None
        self.iv = None
        self.key_uri = None
        self.last_iv = None
        self.last_key_uri = None
        self.event_id = 1
        self.break_timer = None
        self.break_duration = None
        self.m3u8 = "index.m3u8"
        self.lines = []
        self.reload = True
        self.sleep_duration = 0
        self.window_size = None
        self.sliding_window = None
        self.cue_state = None
        self.last_cue = None
        self.headers = []
        self.pts = None
        self.cont_resume = False
        self.hls_pts = "HLS"
        with open(self.sidecar, "w+") as sidecar:  # touch sidecar
            pass

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

    def six2five(self, a_cue):
        """
        six2five converts Time Signals (type 6)
        to SpliceInserts (type 5)
        """
        seg_starts = [0x22, 0x30, 0x32, 0x34, 0x36, 0x38, 0x3A, 0x3C, 0x3E, 0x44, 0x46]
        seg_stops = [0x23, 0x31, 0x33, 0x35, 0x37, 0x39, 0x3B, 0x3D, 0x3F, 0x45, 0x47]
        cue = threefive.Cue(a_cue)
        cue.decode()
        if cue.command.command_type == 6:
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
                        if dscptr.segmentation_type_id in seg_starts:
                            if dscptr.segmentation_duration_flag:
                                duration = dscptr.segmentation_duration
                                out = True
                        else:
                            if dscptr.segmentation_type_id in seg_stops:
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
        with open(self.sidecar, "a") as sidecar:
            sidecar.write(f"{cue.command.pts_time},{cue.encode()}")
        return cue.encode()

    def media_stuff(self):
        media = self.media[-1]
        short_media = media.rsplit("/", 1)[1].split("?", 1)[0]
        return f"\t\t\t Media: {short_media.strip()}"

    def cue_stuff(self):
        return f"{REV}{self.cue_state} {NORM}"

    def diff_stuff(self):
        if not self.break_duration:
            return f"Break Timer: {round(self.break_timer,3)}\n"
        return f"Diff: {round(self.break_timer - self.break_duration,3)}\n"

    def dur_stuff(self):
        return f"Duration: {self.break_duration}\n"

    def add_cue(self, cue, line):
        """
        add_cue determines cue_state and
        calls six2five to replace time signals
        """
        cue = cue.replace("\r", "").replace("\n", "")
        if "CONT" not in line:
            if cue.startswith("#EXT-X-CUE-IN"):
                self.cue_state = "IN"
                print(
                    f"{iso8601()} {self.cue_stuff()}{SUB}{self.diff_stuff()}{self.media_stuff()}"
                )
                self.reset_break()
                return line
            if cue.startswith("#EXT-X-CUE-OUT"):
                self.break_timer == 0.0
                try:
                    self.break_duration = atoif(line.split(":")[1])
                except:
                    pass
                finally:
                    self.cue_state = "OUT"
                print(
                    f"{iso8601()} {self.cue_stuff()}{SUB}{self.dur_stuff()}{self.media_stuff()}"
                )
                return line
        cue2 = self.six2five(cue)
        cue2data = Cue(cue2)
        cue2data.decode()
        line = line.replace(cue, cue2)
        # print(f"{iso8601()} converted {cue} \n-> {cue2}\n")
        return line

    def block(self, line):
        """
        print SCTE-35 tags blocked by the ruleset.
        """
        print(f"{iso8601()}{REV} Skipping {NORM}:{SUB}{line}{self.media_stuff()}")

    def chk_x_cue_out_cont(self, tags, line):
        """
        chk_x_cue_out_const processes
        #EXT-X-CUE-OUT-CONT tags
        """
        cont_tags = tags["#EXT-X-CUE-OUT-CONT"]
        if self.cue_state in ["OUT", "CONT"] or self.cont_resume == True:
            if self.cont_resume:
                print(f"{iso8601()}: {REV} Resuming {NORM} {line}")
            self.cont_resume = False
            self.cue_state = "CONT"
            if self.break_timer is None:
                if "ElapsedTime" in cont_tags:
                    self.break_timer = cont_tags["ElapsedTime"]
                    print(
                        f"{iso8601()}  Setting break timer to {cont_tags['ElapsedTime']}\n"
                    )
                if "Duration" in cont_tags:
                    self.break_duration = cont_tags["Duration"]
                    print(f"{iso8601()}  Setting duration to {cont_tags['Duration']}\n")
            return line
        self.block(line)
        self.cont_resume = True
        return "## " + line

    def chk_x_cue_in(self, tags, line):
        if self.cue_state == "CONT":
            if self.break_timer is not None:
                self.cue_state = "IN"
                line = self.add_cue(line, line)
                self.reset_break()
                return line
        self.block(line)
        return "## " + line

    def chk_x_cue_out(self, tags, line):
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
            return self.add_cue(line, line)
        self.block(line)
        return "## " + line

    def chk_x_scte35(self, tags, line):
        if "CUE" in tags["#EXT-X-SCTE35"]:
            return self.add_cue(tags["#EXT-X-SCTE35"]["CUE"], line)
        return line

    def chk_x_daterange(self, tags, line):
        print("\t\t\t Tags:")
        for k, v in tags["#EXT-X-DATERANGE"].items():
            print(f"\t\t\t\t {k}: {v.strip()}")
        # print(f"\t\t\t Tags:{tags['#EXT-X-DATERANGE']}\n")
        for scte35_tag in ["SCTE35-OUT", "SCTE35-IN"]:
            if scte35_tag in tags["#EXT-X-DATERANGE"]:
                return self.add_cue(tags["#EXT-X-DATERANGE"][scte35_tag], line)
        return line

    def chk_x_oatcls(self, tags, line):
        return self.add_cue(tags["#EXT-OATCLS-SCTE35"], line)

    def scte35(self, line):
        """
        scte35 processes SCTE-35 related tags.
        """
        scte35_map = {
            "#EXT-X-DATERANGE": self.chk_x_daterange,
            "#EXT-X-SCTE35": self.chk_x_scte35,
            "#EXT-X-CUE-OUT-CONT": self.chk_x_cue_out_cont,
            "#EXT-X-DATERANGE": self.chk_x_daterange,
            "#EXT-OATCLS-SCTE35": self.chk_x_oatcls,
            "#EXT-X-CUE-IN": self.chk_x_cue_in,
            "#EXT-X-CUE-OUT": self.chk_x_cue_out,
        }
        tags = TagParser([line]).tags
        for k, v in scte35_map.items():
            if k in line:
                return v(tags, line)
        return line

    def auto_cuein(self, line):
        """
        auto_cuein handles cue.command.auto-return
        """
        if self.cue_state == "CONT":
            if self.break_timer and self.break_duration:
                if self.break_timer >= self.break_duration:
                    self.cue_state = "IN"
                    print(
                        f"{iso8601()} {REV}AUTO CUE-IN{NORM}{SUB}{self.diff_stuff()}{SUB}{self.media_stuff()}"
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
        """
        parse_target_duration reads target duration
        off the manifest to set self.sleep_duration.
        self.sleep_duration is used to throttle manifest
        requests.
        """
        if "TARGETDURATION" in line:
            if self.sleep_duration == 0:
                self.sleep_duration = round(atoif(line.split(":")[1]), 3)
                print(f"\t\t\t Target Duration: {self.sleep_duration}")

    def mk_window_size(self, lines):
        """
        mk_window_size sets the sliding window size
        for the output to match that off the input and
        determine how long to keep media data info
        for segments.
        """
        if not self.window_size:
            self.window_size = len(
                [line for line in lines if line.startswith("#EXTINF:")]
            )
            self.sliding_window.size = self.window_size
            print(f"\t\t\t Window Size: {self.window_size}")

    def update_cue_state(self):
        """
        update_cue_state changes CUE state.
        """
        if self.cue_state == "OUT":
            self.cue_state = "CONT"
        if self.cue_state == "IN":
            self.cue_state = None

    @staticmethod
    def decode_lines(lines):
        """
        decode_lines convert bytes to ascii
        """
        return [line.decode() for line in lines]

    def parse_line(self, line):
        if line.startswith("#EXTINF:"):
            line = self.extinf(line)
            return line
        self.chk_aes(line)
        line = self.scte35(line)
        return line

    def parse_header(self, line):
        splitline = line.split(":", 1)
        if splitline[0] in HEADER_TAGS:
            self.parse_target_duration(line)
            self.headers.append(line)
            return True
        return False

    def chk_endlist(self, line):
        """
        chk_endlist disables manifest reloading
        if line contains ENDLIST tag.
        """
        if "#EXT-X-ENDLIST" in line:
            self.reload = False

    def write_manifest(self):
        """
        write_manifest writes out the
        corrected manifest.
        """
        with open(self.m3u8, "w") as out:
            out.write("#EXTM3U\n")
            out.write("".join(self.headers))
            out.write(self.sliding_window.all_panes())

    def pull(self, manifest):
        """
        pull m3u8 and parse it.
        """
        print(f"\n{REV}{iso8601()}{NORM} {REV}Started{NORM}")
        print(f"\t\t\t Manifest: {manifest}")
        self.base_uri = manifest.rsplit("/", 1)[0]
        self.sliding_window = SlidingWindow()
        while self.reload:
            lines = []
            self.headers = []
            with reader(manifest) as m3u8:
                m3u8_lines = self.decode_lines(m3u8.readlines())
                self.mk_window_size(m3u8_lines)
                for line in m3u8_lines:
                    self.chk_endlist(line)
                    if line.startswith("#"):
                        if not self.parse_header(line):
                            lines.append(line)
                    else:
                        media = line
                        if not media.startswith("http"):
                            media = self.base_uri + "/" + media
                        if self.new_media(media):
                            lines = [self.parse_line(line) for line in lines]
                            pane = Pane(media, lines)
                            self.sliding_window.slide_panes(pane)
                        lines = []
            self.write_manifest()
            self.update_cue_state()
            time.sleep(self.sleep_duration)
        self.write_manifest()


def cli():
    """
    cli is a function to use in a command line tool

        #!/usr/bin/env python3

        from showcues import cli

        if __name__ == "__main__":
            cli()


     is all that's required.
    """
    playlists = None
    m3u8 = None
    with reader(sys.argv[1]) as arg:
        variants = [line for line in arg if b"#EXT-X-STREAM-INF" in line]
        if variants:
            fu = M3uFu()
            reload = False
            fu.m3u8 = sys.argv[1]
            fu.decode()
            playlists = [
                segment
                for segment in fu.segments
                if "#EXT-X-STREAM-INF" in segment.tags
            ]
    if playlists:
        m3u8 = playlists[0].media
    else:
        m3u8 = sys.argv[1]
    cp = CuePuller()
    cp.pull(m3u8)


if __name__ == "__main__":
    cli()
