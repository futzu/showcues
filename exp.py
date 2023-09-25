#!/usr/bin/env python3

# https://c4af3793bf76b33c.mediapackage.us-west-2.amazonaws.com/out/v1/547e1b8d09444666ac810f6f8c78ca82/index.m3u8
import datetime
import sys
import time
from collections import deque
from threefive import Segment, Cue
from m3ufu import M3uFu, TagParser, HEADER_TAGS
from new_reader import reader

REV = "\033[7m"
NORM = "\033[27m"
SUB = "\t\t\t"
NSUB = f"\n{SUB}"
ROLLOVER = 95443.717678


def atoif(value):
    """
    atoif converts ascii to (int|float)
    """
    if "." in value:
        try:
            value = float(value)
            return value
        except:
            pass
    else:
        try:
            value = int(value)
            return value
        except:
            pass
    return None


def iso8601():
    """
    return UTC time in iso8601 format.

    '2023-05-11T15:55:51.'

    """
    return f"{datetime.datetime.utcnow().isoformat()[:-4]}Z "


def validate(cue):
    """
    default validation function
    always returns True
    """
    return True


class Scte35Profile:
    def __init__(self, func=validate):
        """
        A Scte35Profile
        
        
        """
        self.parse_segments = False
        self.parse_manifests = True 
        self.hls_tags =["#EXT-OATCLS-SCTE35",
                        ] #"#EXT-X-DATERANGE","#EXT-X-SCTE35",
                          # "#EXT-X-CUE-IN","#EXT-X-CUE-OUT-CONT",] 
        self.commands_types =[6,]
        self.descriptor_tags = [2,]
        self.starts = [0x22, 0x30, 0x32, 0x34, 0x36, 0x38,]
        self.stops = [0x23, 0x31, 0x33, 0x35, 0x37, 0x39,]
        self.validation_func = func

    def set_pts(self,cue):
        pts = cue.command.pts_time + cue.info_section.pts_adjustment
        return pts % ROLLOVER

    def validate_cue(self,cue, func=validate):
        pts = None
        line = None
        cue.decode()
        if not self.validation_func(cue):
            return pts,line
        if cue.command.command_type in self.commands_types:
            if "pts_time" in vars(cue.command) and cue.command.pts_time:
                pts = self.set_pts(cue)
                cue.show()
            if cue.command.command_type == 5:                
                line =self.validate_splice_insert(cue)
        if cue.command.command_type ==6:
                line = self.validate_time_signal(cue)
        return pts,line

    def validate_splice_insert(self,cue):
        line = None
        if cue.command.out_of_network_indicator:
            if "break_duration" in vars(cue.command) and cue.command.break_duration:
               duration = cue.command.break_duration
               line = f'#EXT-X-CUE-OUT:{duration}'
               return line
        else:
            line ="#EXT-X-CUE-IN"
            return line
        return line

    def validate_time_signal(self,cue):
        line = None
        for dscptr in cue.descriptors:
            if dscptr.tag in self.descriptor_tags:
                if dscptr.segmentation_type_id in self.starts:
                    if "segmentation_duration" in vars(dscptr):
                        duration = dscptr.segmentation_duration
                        line = f'#EXT-X-CUE-OUT:{duration}'
                        return line
                if dscptr.segmentation_type_id in self.stops:
                    line ="#EXT-X-CUE-IN"
                    return line
        return line                                
  
class Pane:
    """
    Pane class. Sliding_Window slides Panes
    """

    def __init__(self, media, lines):
        self.media = media
        self.lines = lines

    def get(self):
        """
        get merges self.lines and self.media for
        writing m3u8 files.
        """
        all_lines = self.lines + [self.media]
        return "".join(all_lines)


class SlidingWindow:
    """
    The Sliding Window class
    """

    def __init__(self, size=101):
        self.size = size
        self.panes = deque()
        self.delete = False

    def pop_pane(self):
        """
        pop_pane removes the first item in self.panes
        """
        if len(self.panes) > self.size:
            self.panes.popleft()

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


class AacParser:
    applehead = b"com.apple.streaming.transportStreamTimestamp"

    @staticmethod
    def is_header(header):
        """
        is_header tests aac and ac3 files for ID3 headers.
        """
        if header[:3] == b"ID3":
            return True
        return False

    @staticmethod
    def id3_len(header):
        """
        id3_len parses the length value from ID3 headers
        """
        id3len = int.from_bytes(header[6:], byteorder="big")
        return id3len

    @staticmethod
    def syncsafe5(somebytes):
        """
        syncsafe5 parses PTS from ID3 tags.
        """
        lsb = len(somebytes) - 1
        syncd = 0
        for idx, b in enumerate(somebytes):
            syncd += b << ((lsb - idx) << 3)
        return round(syncd / 90000.0, 6)

    def parse(self, media):
        """
        aac_pts parses the ID3 header tags in aac and ac3 audio files
        """
        aac = reader(media)
        header = aac.read(10)
        if self.is_header(header):
            id3len = self.id3_len(header)
            data = aac.read(id3len)
            pts = 0
            if self.applehead in data:
                try:
                    pts = float(data.split(self.applehead)[1].split(b"\x00", 2)[1])
                except:
                    pts = self.syncsafe5(data.split(self.applehead)[1][:9])
                finally:
                    self.first_segment = False
                    return round((pts % ROLLOVER), 6)


class CuePuller:
    def __init__(self):
        self.media = deque()
        self.sidecar = "exp-sidecar.txt"
        self.m3u8 = "exp.m3u8"
        self.base_uri = None
        self.iv = None
        self.key_uri = None
        self.last_iv = None
        self.last_key_uri = None
        self.break_timer = None
        self.break_duration = None
        self.reload = True
        self.sleep_duration = 0
        self.window_size = None
        self.sliding_window = SlidingWindow()
        self.cue_state = None
        self.last_cue = None
        self.headers = []
        self.pts = 0
        self.cont_resume = False
        self.first_segment = True
        self.hls_pts = "HLS"
        self.prof = Scte35Profile()
        with open(self.sidecar, "w+") as sidecar:  # touch sidecar
            pass

    @staticmethod
    def clear():
        """
        clear previous line.
        """
        print(" " * 80, end="\r")
        print(" " * 80, file=sys.stderr, end="\r", flush=True)

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

    def to_sidecar(self, pts,line):
        """
        to_sidecar writes pts,cue pairs to the sidecar file.
        """
        with open(self.sidecar, "a") as sidecar:
            sidecar.write(f"{pts},{line}\n")

    def media_stuff(self):
        """
        media_stuff trims segment URI to just the file name.
        """
        media = self.media[-1]
        short_media = media.rsplit("/", 1)[1].split("?", 1)[0]
        return f"{NSUB}Media: {short_media.strip()}"

    def cue_stuff(self):
        """
        cue_stuff returns self.cue_state formated.
        """
        return f"{REV}{self.cue_state} {NORM}"

    def diff_stuff(self):
        """
        diff stuff returns formated self.break_timer
        and if possible the difference between the actual break duration
        and the specified SCTE-35 break duration.
        """
        if self.break_timer is not None:
            if not self.break_duration: 
                return f"{NSUB}Break Timer: {round(self.break_timer,6)}"
            return f"{NSUB}Diff: {round(self.break_timer - self.break_duration,6)}"
        return ""


    def dur_stuff(self):
        """
        dur_stuff returns self.break_duration formated.
        """
        return f"{NSUB}Duration: {self.break_duration}"

    def pts_stuff(self):
        """
        pts_stuff returns  PTS formated.
        """
        return f"{NSUB}{self.hls_pts}: {self.pts}"

    def set_cue_state(self, cue, line):
        """
        set_cue_state determines cue_state

        """
        if cue.encode() == self.last_cue:
            return ""
        self.last_cue = cue.encode()
        cue = cue.replace("\r", "").replace("\n", "")
        line = line.replace("\n", "")
        if "CONT" not in line:
            head = f"\n{iso8601()}{self.cue_stuff()}{self.pts_stuff()}{NSUB}Tag: {line}"
            if line.startswith("#EXT-X-CUE-IN"):
                if self.break_duration and self.break_timer:
                    if self.break_timer /self.break_duration <0.9:
                        return self.invalid(line)
                self.cue_state = "IN"
                self.to_sidecar(self.pts,line)
                self.clear()
                print(f"{head}{self.diff_stuff()}{self.media_stuff()}\n")
                self.reset_break()
                return line
            if line.startswith("#EXT-X-CUE-OUT"):
                self.break_timer = 0.0
                try:
                    self.break_duration = atoif(line.split(":")[1])
                except:
                    pass
             #   finally:
                self.to_sidecar(self.pts,line)
                self.cue_state = "OUT"
                self.clear()
                print(f"{head}{self.dur_stuff()}{self.media_stuff()}\n")
                return line
        return self.invalid(line)

    def invalid(self, line):
        """
        invalid print invalid SCTE-35 HLS tags
        """
        self.clear()
        line = line.replace("\n", "")
        print(
            f"\n{iso8601()}{REV}Invalid{NORM}{self.pts_stuff()}{NSUB}Tag: {line}{self.media_stuff()}\n"
        )
        return "## " + line

    def show_tags(self, tags):
        try:
            for k, v in tags.items():
                print(f"{SUB}{k}: {v}")
        except:
            return

    def _set_break_timer(self, line, cont_tags):
        if self.break_timer is None:
            if "ElapsedTime" in cont_tags:
                self.break_timer = cont_tags["ElapsedTime"]
            else:
                try:
                    self.break_timer = float(line.split(":", 1)[1].split("/")[0])
                except:
                    self.break_timer = 0.0
            print(f"{iso8601()}{REV}Setting{NORM} Break Timer to {self.break_timer}\n")

    def _set_break_duration(self, line, cont_tags):
        if "Duration" in cont_tags:
            self.break_duration = cont_tags["Duration"]
        else:
            try:
                self.break_duration = float(line.split(":", 1)[1].split("/")[1])
            except:
                self.break_duration = None
        if self.break_duration:
            print(
                f"{iso8601()}{REV}Setting{NORM} Break Duration to {self.break_duration}\n"
            )

    def chk_x_cue_out_cont(self, tags, line):
        """
        chk_x_cue_out_const processes
        #EXT-X-CUE-OUT-CONT tags
        """
        cont_tags = tags["#EXT-X-CUE-OUT-CONT"]
        if self.cue_state not in ["OUT", "CONT"] and not self.first_segment:
            return self.invalid(line)
        if self.first_segment:
            print(f"{iso8601()}{REV}Resuming Ad Break{NORM}\n")
        self.cue_state = "CONT"
        self._set_break_timer(line, cont_tags)
        self._set_break_duration(line, cont_tags)
        return line

    def chk_x_cue_in(self, tags, line):
        """
        chk_x_cue_in processes
        #EXT-X-CUE-IN tags.
        """
        if self.cue_state in ["OUT", "CONT"]:
            self.cue_state = "IN"
            line = self.set_cue_state(line, line)
            self.reset_break()
            return line
        return self.invalid(line)

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
            return self.set_cue_state(line, line)
        return self.invalid(line)

    def chk_x_scte35(self, tags, line):
        """
        chk_x_scte35 handles #EXT-X-SCTE35 tags.
        """
        if "CUE" in tags["#EXT-X-SCTE35"]:
            cue = Cue(tags["#EXT-X-SCTE35"]["CUE"])
            pts,new_line = self.prof.validate_cue(cue)
            if pts and new_line:
                return self.set_cue_state(tags["#EXT-X-SCTE35"]["CUE"], new_line)
        return self.invalid(line)

    def chk_x_daterange(self, tags, line):
        """
        chk_x_daterange handles #EXT-X-DATERANGE tags.
        """
        self.show_tags(tags["#EXT-X-DATERANGE"])
        #   print()
        for scte35_tag in ["SCTE35-OUT", "SCTE35-IN"]:
            if scte35_tag in tags["#EXT-X-DATERANGE"]:
                cue = Cue(tags["#EXT-X-DATERANGE"][scte35_tag])
                pts,new_line = self.prof.validate_cue(cue)
                if pts and new_line:
                    return self.set_cue_state(tags["#EXT-X-DATERANGE"][scte35_tag], new_line)
        return self.invalid(line)

    def chk_x_oatcls(self, tags, line):
        """
        chk_x_oatcls handles
        #EXT-OATCLS-SCTE35
        HLS tags.
        """
        cue=Cue(tags["#EXT-OATCLS-SCTE35"])
        pts,new_line = self.prof.validate_cue(cue)
        print(pts,new_line)
        if pts and new_line:
            if abs(pts -self.pts) > 5:  # Handle NBC Cues out of sync with video PTS
                pts = self.pts
           # self.to_sidecar(pts,new_line)                
            return self.set_cue_state(tags["#EXT-OATCLS-SCTE35"], new_line)
        return self.invalid(line)

    def scte35(self, line):
        """
        scte35 processes SCTE-35 related tags.
        """
        scte35_map = {
            "#EXT-X-DATERANGE": self.chk_x_daterange,
            "#EXT-X-SCTE35": self.chk_x_scte35,
            "#EXT-X-CUE-OUT-CONT": self.chk_x_cue_out_cont,
            "#EXT-OATCLS-SCTE35": self.chk_x_oatcls,
            "#EXT-X-CUE-IN": self.chk_x_cue_in,
            "#EXT-X-CUE-OUT": self.chk_x_cue_out,
        }
        tags = TagParser([line]).tags
        if self.prof.parse_manifests:
            for k, v in scte35_map.items():
                if k in line and  k in self.prof.hls_tags:
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
                    self.clear()
                    print(
                        f"{iso8601()}{REV}AUTO CUE-IN{NORM}{self.pts_stuff()}{self.diff_stuff()}{self.media_stuff()}\n"
                    )
                    self.reset_break()
                    self.to_sidecar(self.pts, "\n#AUTO\n#EXT-X-CUE-IN\n")
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
            seg_time = round(atoif(tags["#EXTINF"]), 6)
            line = self.auto_cuein(line)
            if self.pts is not None:
                self.pts += seg_time
            if self.break_timer is not None:
                self.break_timer += seg_time
        return line

    def print_time(self):
        """
        print_time prints wall clock and pts.
        """
        stuff = ""
        if self.break_timer:
            stuff = f"{REV}Break{NORM} {round(self.break_timer,3)}"
            if self.break_duration:
                stuff = f"{stuff} / {round(self.break_duration,3)}"
        self.clear()
        print(
            f"\r\r{iso8601()}{REV}{self.hls_pts}{NORM} {self.pts} {stuff}",
            end="\r\r",
            file=sys.stderr,
            flush=True,
        )

    def _ts_splice_insert(self, cue):
        inout = None
        duration = None
        if cue.command.command_type == 5:
            inout = "IN"
            if cue.command.out_of_network_indicator:
                inout = "OUT"
                if "break_duration" in vars(cue.command):
                    duration = cue.command.break_duration
        return inout, duration

    def _ts_time_signal(self, cue):
        inout = None
        duration = None
        segStarts = [0x22, 0x30, 0x32, 0x34, 0x36, 0x38]
        segStops = [0x23, 0x31, 0x33, 0x35, 0x37, 0x39]
        if cue.command.command_type == 6:
            for dscptr in cue.descriptors:
                if dscptr.tag == 2:
                    if dscptr.segmentation_type_id in segStarts:
                        inout = "OUT"
                        if "segmentation_duration" in vars(dscptr):
                            duration = dscptr.segmentation_duration
                    if dscptr.segmentation_type_id in segStops:
                        inout = "IN"
        return inout, duration

    def ts_cue_stuff(self, cue):
        cue_stuff = ""
 #       if cue.encode() == self.last_cue:
   #       return cue_stuff
   #     self.last_cue = cue.encode()
        inout, duration = self._ts_splice_insert(cue)
        if not inout:
            inout, duration = self._ts_time_signal(cue)
        cue.decode()
        cue_stuff = f"Command: {cue.command.name}"
        if inout:
            cue_stuff = f"{cue_stuff} {inout}"
        if duration:
            cue_stuff = f"{cue_stuff}{NSUB}Duration: {duration}"
        return cue_stuff

    def chk_ts(self, this):
        """
        chk_ts  check MPEGTS for PTS and SCTE-35.
        """
        if ".ts" in this:
            if self.first_segment:
                Segment(this, key_uri=self.key_uri, iv=self.iv).show()
                print()
                self.first_segment = False
            seg = Segment(this, key_uri=self.key_uri, iv=self.iv)
            seg.shushed()
            seg.decode()
            if seg.pts_start:
                self.pts = seg.pts_start
                self.print_time()
                self.hls_pts = "PTS"
            if self.prof.parse_segments:
                for cue in seg.cues:
                    if "pts" in vars(cue.packet_data) and cue.packet_data.pts:
                        self.pts = cue.packet_data.pts
                    if cue.encode() != self.last_cue:
                        self.last_cue = cue.encode()
                        cue_pts,line = self.prof.validate_cue(cue)
                        if cue_pts and line:
                            self.to_sidecar(cue_pts,line)
                            self.set_cue_state(cue.encode(),line)
                            cue_stuff = self.ts_cue_stuff(cue)
                            self.clear()
                            print(
                            f"\n{iso8601()}{REV}SCTE-35{NORM}{NSUB}Current PTS: {round(self.pts,6)}{NSUB}PreRoll: {round(cue_pts - self.pts,6)}{NSUB}Splice Point: {round(cue_pts,6)}{NSUB}{cue_stuff}{self.media_stuff()}\n"
                            )
            self.print_time()

    def chk_aac(self, this):
        """
        chk_aac check aac and ac3  HLS audio segments
        for PTS in ID3 header tags.
        """
        if ".aac" in this or ".ac3" in this:
            aac_parser = AacParser()
            self.first_segment = False
            pts = aac_parser.parse(this)
            if pts:
                self.pts = pts
                self.hls_pts = "PTS"
                self.print_time()

    def new_media(self, this):
        """
        new_media check to see
        if the media is new in a
        live sliding window
        """
        if this not in self.media:
            self.media.append(this)
            if len(self.media) > self.window_size + 1:
                self.media.popleft()
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
                target_duration = atoif(line.split(":")[1])
                self.sleep_duration = round(target_duration * 0.01, 3)
                print(f"{SUB}Target Duration: {target_duration}\n")

    def mk_window_size(self, lines):
        """
        mk_window_size sets the sliding window size
        for the output to match that off the input and
        determine how long to keep media data info
        for segments.
        """
        if not self.window_size:
            self.window_size = len([line for line in lines if "#EXTINF:" in line])
            self.sliding_window.size = self.window_size
            print(f"{SUB}Window Size: {self.window_size}")

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
        if "#EXTINF:" in line:
            line = self.extinf(line)
            return line
        self.chk_aes(line)
        line = self.scte35(line)
        return line

    def parse_header(self, line):
        """
        parse_headers parses m3u8 files for HLS header tags.
        """
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

    def _parse_manifest(self, manifest):
        with reader(manifest) as m3u8:
            lines = []
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
                        media = media.replace("\n", "")
                        self.chk_ts(media)
                        self.chk_aac(media)
                        pane = Pane(media, lines)
                        self.sliding_window.slide_panes(pane)
                    lines = []
        self.update_cue_state()
        time.sleep(self.sleep_duration)

    def pull(self, manifest):
        """
        pull m3u8 and parse it.
        """
        print(f"\n{iso8601()}{REV}Started{NORM}")
        print(f"{SUB}Manifest: {manifest}")
        self.base_uri = manifest.rsplit("/", 1)[0]
        self.sliding_window = SlidingWindow()
        while self.reload:
            self._parse_manifest(manifest)


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
            fu.m3u8 = sys.argv[1]
            fu.decode()
            playlists = [
                segment
                for segment in fu.segments
                if "#EXT-X-STREAM-INF" in segment.tags
            ]
    if playlists:
        m3u8 = playlists[0].media
        m3u8 = "https" + m3u8.split("https")[-1]
    else:
        m3u8 = sys.argv[1]
    cp = CuePuller()
    cp.pull(m3u8)
    print()


if __name__ == "__main__":
    cli()







  
