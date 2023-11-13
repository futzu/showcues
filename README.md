# showcues is a tool for debugging SCTE-35 in HLS.

* Display HLS CUE-OUT and CUE-IN tags with wall clock times.
* Displays SCTE-35 Cues from SCTE-35 streams in MPEGTS segments.
* Displays invalid SCTE=35 HLS Tags.
* Displays Break duration and diff.
* Automatic AES Decryption for MPEGTS segments.
* Parses PTS from MPEGTS as well as AAC and AC3 ID3 headers.
 
#  Latest Version is `1.0.41`
 [showcues cyclomatic complexity score: __A (2.81)__](cc.md)
 


```lua
2023-09-10T01:56:07.06Z Started
			Manifest: https://example.com/index.m3u8
			Window Size: 5
			Target Duration: 3

2023-09-10T01:56:07.06Z Resuming Ad Break
2023-09-10T01:56:07.06Z Setting Break Timer to 2.0
2023-09-10T01:56:07.06Z Setting Break Duration to 119.986533

Program: 1
    Service:	
    Provider:	
    Pid:	480
    Pcr Pid:	481
    Streams:
		Pid: 481[0x1e1]	Type: 0x1b AVC Video
		Pid: 482[0x1e2]	Type: 0xf AAC Audio
		Pid: 483[0x1e3]	Type: 0x86 SCTE35 Data
		Pid: 484[0x1e4]	Type: 0x15 ID3 Timed Meta Data
```
```rebol
      
2023-11-13T01:17:39.83Z #EXT-X-CUE-OUT:60.0
			PTS: 49321.142044 (Splice Point)
			Duration: 60.0
			Media: index_2_3332800.ts

                                                                                                                                                         
2023-11-13T01:17:39.83Z SCTE-35
			Stream PTS: 49321.142044
			PreRoll: 9.400011
			Splice Point: 49330.542055
			Type: Splice Insert
			Media: index_2_3332800.ts
                                                                                                                                                 
2023-11-13T01:18:21.92Z AUTO CUE-IN
			PTS: 49379.175378
			Timer: 60.0
			Duration: 60.0
			Diff: 0.0
			Media: index_2_3332812.ts
             
```

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

showcues https://nmxlive.akamaized.net/hls/live/529965/Live_1/index.m3u8
```

[ Help ]
 
    To display help:
    
	showcues help 
	

[ Input ]

**showcues** takes an m3u8 URI as input.

* M3U8 formats supported:

    * master  ( When a master.m3u8 used, showcues parses the first rendition it finds )
  * rendition 
        	
* Segment types supported:

    * AAC
    * AC3
    * MPEGTS

* Protocols supported:
    * file
    * http(s)
	* UDP 
	* Multicast

    	Encryption supported:
		
		* AES-128 (segments are automatically decrypted) 	

[ SCTE-35 ]

showcues displays SCTE-35 Embedded Cues as well as SCTE-35 HLS Tags.

 Supported SCTE-35:

* All Commands, Descriptors, and UPIDS
          in the 2022-b SCTE-35 specification.

* Supported HLS Tags
    * #EXT-OATCLS-SCTE35
    * #EXT-X-CUE-OUT-CONT
    * #EXT-X-DATERANGE
	* #EXT-X-SCTE35
	* #EXT-X-CUE-IN
    * #EXT-X-CUE-OUT


[ SCTE-35 Parsing Profiles]

Parsing profiles allows you to adjust how showcues parses SCTE-35.


running the command:

	`showcues profile`

will generate a default profile and write a file named sc.profile
in the current working directory.
```rebol
a@fu:~$ cat sc.profile

	expand_cues = False
	parse_segments = False
	parse_manifests = True
	hls_tags = #EXT-OATCLS-SCTE35,#EXT-X-CUE-OUT-CONT,
	#EXT-X-DATERANGE,#EXT-X-SCTE35,#EXT-X-CUE-IN,#EXT-X-CUE-OUT
	command_types = 0x6,0x5
	descriptor_tags = 0x2
	starts = 0x22,0x30,0x32,0x34,0x36,0x44,0x46
```
<br/>`expand_cues`:	   set to True to show cues fully expanded as JSON
<br/>

`parse_segments`:    set to true to enable parsing SCTE-35 from MPEGTS.
<br/>

`parse_manifests`:   set to true to parse the m3u8 file for SCTE-35 HLS Tags.
<br/>
  
`hls_tags`:          set which SCTE-35 HLS Tags to parse.
<br/>

`command_types`:     set which Splice Commands to parse.
<br/>

`descriptor_tags`:   set which Splice Descriptor Tags to parse.
<br/>

`starts`:            set which Segmentation Type IDs to use to start breaks.
<br/>



    		Edit the file as needed and then run showcues.


[ Profile Formatting Rules ]

* Values do not need to be quoted.

* Multiple values are separated by a commas.

* No partial line comments. Comments must be on a separate lines.

* Comments can be started with a # or //

* Integers can be base 10 or base 16


[ Output Files ]

* Created in the current working directory
* Clobbered on start of showc ues

* Profile rules applied to the output:
   *	sc.m3u8  - live playable rewrite of the m3u8
   * sc.sidecar - list of ( pts, HLS SCTE-35 tag ) pairs

* Profile rules not applied to the output:	
    	      * sc.dump  -  all of the HLS SCTE-35 tags read.
	      * sc.flat  - every time an m3u8 is reloaded,
                           it's contents are appended to sc.flat. 

[ Cool Features ]

* showcues can resume when started in the middle of an ad break.

            2023-10-13T05:59:50.24Z Resuming Ad Break
            2023-10-13T05:59:50.34Z Setting Break Timer to 17.733
            2023-10-13T05:59:50.44Z Setting Break Duration to 60.067

* mpegts streams are listed on start ( like ffprobe )

            Program: 1
                Service:	
                Provider:	
                Pid:	480
                Pcr Pid:	481
                Streams:
                    Pid: 481[0x1e1]	Type: 0x1b AVC Video
                    Pid: 482[0x1e2]	Type: 0xf AAC Audio
                    Pid: 483[0x1e3]	Type: 0x86 SCTE35 Data
                    Pid: 484[0x1e4]	Type: 252 Unknown
                    Pid: 485[0x1e5]	Type: 0x15 ID3 Timed Meta Data


[ Example Usage ]

* Show this help:		

		showcues help

* Generate a new sc.profile
	    
		showcues profile

* parse an m3u8

    		showcues  https://example.com/out/v1/547e1b8d09444666ac810f6f8c78ca82/index.m3u8
           
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
