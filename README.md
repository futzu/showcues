# showcues
Display HLS CUE-OUT and CUE-IN tags  with wall clock times.

 Latest Version is `1.0.5`

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
set duration to  150.0
2023-06-25T08:44:39 OUT #EXT-X-CUE-OUT:150.000 
Media: https://3ae97e9482b0d011.mediapackage.us-west-2.amazonaws.com/out/v1/42be1df466a74177885d7ad299c0bb41/index_1_790188.ts?m=1683044685
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
![image](https://github.com/futzu/showcues/assets/52701496/ec8a3748-bba6-4b4a-b2e0-08edae1534eb)
