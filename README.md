# showcues
Display HLS CUE-OUT and CUE-IN tags with wall clock times.

 Latest Version is `1.0.11`

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
    * Wall Clock Time
    * PTS 
    * Duration
    * The Segment URI
  
```smalltalk
2023-08-23T08:58:20.92Z  OUT                                                    
			 PTS: 38113.435878
			 Duration: 90.023267
			 Media: seg9.ts

```

* A `CUE-IN` is shown with
    * Wall Clock Time
    * PTS
    * The Diff of when the CUE-IN should be and when it actually occurs.
    * The Segment URI 
```smalltalk
2023-08-23T08:58:21.02Z  IN                                                     
			 PTS: 38203.175533
			 Diff: -0.033
			 Media: seg43.ts

```
  * An `AUTO CUE-IN` such as with a Break Auto Return, includes the word `AUTO`
```smalltalk
2023-06-19T03:03:47 AUTO #EXT-X-CUE-IN  Diff: 5.539 
Media: index_375_00039.ts
```
* A `SCTE-35` indicates SCTE-35 data in the segments. A `SCTE-35` is shown with:
  * Wall Clock Time
  * PTS
  * The Base64 encoded SCTE-35 Cue 
  
```smalltalk
2023-08-23T08:58:20.91Z  SCTE-35                                                
			 PTS: 38113.135578
			 Cue:/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==

```

* Live clock at the bottom of the page.
  * Wall Clock Time
  * PTS
```smalltalk
 2023-08-23T08:58:21.07Z PTS:38247.104111
```

* A Sidecar file, `sidecar.txt` is generated containing a list of ( pts,cue ) pairs.
```rebol
a@debian:~/tunein/showcues$ tail -f sidecar.txt 
58363.607489,/DBFAAH/7S+YAP/wFAUAAAABf+//ORY3wv4AzgQwmZkBAQAgAh5DVUVJAAAAAH/AAADN/mABCDEwMTAwMDAwNAAAAADgrVWi
59305.014622,/DBFAAH/7S+YAP/wFAUAAAABf+//PiMLNP4ApMbEmZkBAQAgAh5DVUVJAAAAAH/AAACky4ABCDEwMTAwMDAwNAAAAAClR6us
59595.771756,/DBFAAH/7S+YAP/wFAUAAAABf+//P7JWgv4Azey6mZkBAQAgAh5DVUVJAAAAAH/AAADN/mABCDEwMTAwMDAwNAAAAAC+xYYV
```
