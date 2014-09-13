hrtf_audio
==========

dependencies: 
    csound (tested using 5.17 via Debian repo)
    scikits audiolab (tested using version 0.11.0)
    numpy (tested using version 1.8.0)

usage: 
```
python clicktrain_hrtf.py f0 duration
```

where "f0" is in Hz and "duration" is in seconds, will generate spatialized
click trains in the processedWavs folder.  There will be individual wav files
for azimuth -90 to +90 degrees, with 0.1 degree spacing, all at elevation 0
degrees.
