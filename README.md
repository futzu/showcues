```smalltalk
                                                                                
2023-08-29T10:30:19.39Z OUT 
			PTS: 72829.7572
			Media: seg81.ts
			Duration: 119.986533
                                                                                
2023-08-29T10:30:19.43Z IN 
			PTS: 72947.8752
			Media: seg140.ts
			Diff: 0.064734
                                                                                
2023-08-29T10:30:19.43Z SCTE-35
			PTS: 72949.8772
			Media: seg141.ts
			Cue: /DAsAAAAAyiYAP/wCgUAAAABf1+ZmQEBABECD0NVRUkAAAAAf4ABADUAAC2XQZU=
                                                                                
2023-08-29T10:30:19.43Z Invalid
			PTS: 72955.8832
			Media: seg144.ts
			Tag: #EXT-X-CUE-IN

```

# showcues is a tool for debugging SCTE-35 in HLS.
* Display HLS CUE-OUT and CUE-IN tags with wall clock times.
* Displays SCTE-35 Cues from SCTE-35 streams in MPEGTS segments.
* Displays invalid SCTE=35 HLS Tags.
* Displays Break duration and diff.
* Automatic AES Decryption for MPEGTS segments.
* Parses PTS from MPEGTS as well as AAC and AC3 ID3 headers.
 
##  Latest Version is `1.0.15`

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
   *  Incorrect HLS Tags ate reported as invalid. 
   * Missing CUE-INs from break auto-returns are automatically added.
   
```rebol

showcues https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/index.m3u8
# OR
showcues https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/index_1.m3u8

```
### CUE-OUT
* A `CUE-OUT` is shown with:
   * Wall Clock Time
   * PTS 
   * Duration
   * The Segment URI
  
```smalltalk
2023-08-29T10:30:19.39Z OUT 
			PTS: 72829.7572
			Media: seg81.ts
			Duration: 119.986533
                                                             
```

### CUE-IN
*  A `CUE-IN` is shown with:
  * Wall Clock Time
    * PTS
    * The Segment URI
    * The Diff of when the CUE-IN should be and when it actually occurs.

```smalltalk
2023-08-29T10:30:19.43Z IN 
			PTS: 72947.8752
			Media: seg140.ts
			Diff: 0.064734

```

### AUTO CUE-IN
  * An `AUTO CUE-IN` such as with a Break Auto Return, includes the word `AUTO`
```smalltalk
2023-06-19T03:03:47 AUTO #EXT-X-CUE-IN  Diff: 5.539 
Media: index_375_00039.ts
```

### SCTE-35
* A `SCTE-35` indicates SCTE-35 data in the segments. A `SCTE-35` label is shown with:
  	* Wall Clock Time
  	* PTS
  	* The Segment URI
  	* The Base64 encoded SCTE-35 Cue 
  
```smalltalk
2023-08-29T10:30:19.43Z SCTE-35
			 PTS: 72949.8772
			 Media: seg141.ts
			 Cue: /DAsAAAAAyiYAP/wCgUAAAABf1+ZmQEBABECD0NVRUkAAAAAf4ABADUAAC2XQZU=

```

### Invalid
* `Invalid` indicates an invalid HLS CUE Tag, such as two consecutive CUE-IN tags. An Invalid label includes:  
   	* Wall Clock Time
   	* PTS
   	* The Segment URI
   	* The invalid HLS tag.
```smalltalk
2023-08-29T10:30:19.43Z Invalid
			 PTS: 72955.8832
			 Media: seg144.ts
			 Tag: #EXT-X-CUE-IN


```

### Live Clock
* Live clock at the bottom of the page.
  	* Wall Clock Time
  	* PTS
```smalltalk
 2023-08-23T08:58:21.07Z PTS:38247.104111
```
### Sidecar
* A Sidecar file, `sidecar.txt` is generated containing a list of ( pts,cue ) pairs.
```rebol
a@debian:~/tunein/showcues$ tail -f sidecar.txt 
58363.607489,/DBFAAH/7S+YAP/wFAUAAAABf+//ORY3wv4AzgQwmZkBAQAgAh5DVUVJAAAAAH/AAADN/mABCDEwMTAwMDAwNAAAAADgrVWi
59305.014622,/DBFAAH/7S+YAP/wFAUAAAABf+//PiMLNP4ApMbEmZkBAQAgAh5DVUVJAAAAAH/AAACky4ABCDEwMTAwMDAwNAAAAAClR6us
59595.771756,/DBFAAH/7S+YAP/wFAUAAAABf+//P7JWgv4Azey6mZkBAQAgAh5DVUVJAAAAAH/AAADN/mABCDEwMTAwMDAwNAAAAAC+xYYV
```
