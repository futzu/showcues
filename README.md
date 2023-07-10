# showcues
Display HLS CUE-OUT and CUE-IN tags with wall clock times.

 Latest Version is `1.0.9`

## Install 
* Use pip to install
```rebol
python3 -mpip install showcues 
# and / or 
pypy3 -mpip install showcues
```
## Upgrade
* Use pip to upgrade
```rebol
python3 -mpip install --upgrade showcues 
# and / or 
pypy3 -mpip install  --upgrade showcues
```

## Run 
* showcues takes a master m3u8 OR variant m3u8 _(new with v.1.0.5)_ as input.
* showcues displays where the SCTE-35 cues are based on the SCTE-35 data.
* showcues follows the rules we will be applying to SCTE-35 in HLS. 
   * Cues that are completely wrong are dropped.
   * Missing CUE-INs from break auto-returns are automatically added.
   
```rebol

showcues https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/index.m3u8
# OR
showcues https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/index_1.m3u8

```

* A `CUE-OUT` is shown with:
    * duration
    * wall clock time
    * The segment URI 
```smalltalk

2023-06-26T08:30:57 OUT #EXT-X-CUE-OUT:164.967  Duration: 164.967 
Media: https://c75a7e79204e539d.mediapackage.us-east-1.amazonaws.com/out/v1/9cffbbcc0e8a4fb0b83036cc3b1c5c1f/index_1_773858.aac?m=1683126814

```

* A `CUE-IN` is shown with
    * wall clock time
    * The diff of when the CUE-IN should be and when it actually occurs.
    * The segment URI 
```smalltalk
2023-06-22T02:17:26 IN #EXT-X-CUE-IN   Diff: 0.0
Media: https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/20230606T041328/index_2400/00115/index_2400_01720.ts

```
  * An `AUTO CUE-IN` such as with a Break Auto Return, includes the word `AUTO`
```smalltalk
2023-06-19T03:03:47 AUTO #EXT-X-CUE-IN  Diff: 5.539 
Media: https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/20230606T041328/index_375/00094/index_375_00039.ts
```

* A Sidecar file, `sidecar.txt` is generated containing a list of ( pts,cue ) pairs.
```rebol
a@debian:~/tunein/showcues$ tail -f sidecar.txt 
58363.607489,/DBFAAH/7S+YAP/wFAUAAAABf+//ORY3wv4AzgQwmZkBAQAgAh5DVUVJAAAAAH/AAADN/mABCDEwMTAwMDAwNAAAAADgrVWiNone,/DAsAAH/6gcAAP/wCgUAAAABf1+ZmQEBABECD0NVRUkAAAAAf4ABADUAAN4pJU4=
59305.014622,/DBFAAH/7S+YAP/wFAUAAAABf+//PiMLNP4ApMbEmZkBAQAgAh5DVUVJAAAAAH/AAACky4ABCDEwMTAwMDAwNAAAAAClR6usNone,/DAsAAH/6gcAAP/wCgUAAAABf1+ZmQEBABECD0NVRUkAAAAAf4ABADUAAN4pJU4=
59595.771756,/DBFAAH/7S+YAP/wFAUAAAABf+//P7JWgv4Azey6mZkBAQAgAh5DVUVJAAAAAH/AAADN/mABCDEwMTAwMDAwNAAAAAC+xYYV
```
