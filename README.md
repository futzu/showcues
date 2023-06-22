# showcues
Display HLS CUE-OUT and CUE-IN tags  with wall clock times.

## Install 
* Use pip to install
```rebol
python3 -mpip install showcues 
# and / or 
pypy3 -mpip install showcues
```

## Run 
* showcues takes a master m3u8 file as input, it parses the first playable variant it finds.
```rebol

showcues https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/index.m3u8
```

* showcues displays the variant it picked to parse.
```rebol
https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/index_2400.m3u8
```
* A `CUE-OUT` is shown with:
    * duration
    * wall clock time
    * The segment URI 
```smalltalk
set duration to  360.16
2023-06-19T02:57:40 OUT #EXT-X-CUE-OUT:360.160
Media: https://nmxtunein.akamaized.net/hls/live/2020471/Live_1/20230606T041328/index_375/00093/index_375_01977.ts
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
## Screen Shot
![image](https://github.com/futzu/showcues/assets/52701496/01a59b89-9baa-40a2-86ea-31d39924912f)
