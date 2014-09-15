hrtf_audio
==========

dependencies: 
    csound (tested using 5.17 via Debian repo)
    scikits audiolab (tested using version 0.11.0)
    numpy (tested using version 1.8.0)

usage: 
```
python binaural_stimuli.py timbre duration f0
```

"timbre" is one of [impulse, clicktrain, puretone, sawtooth]

"f0" is the fundamental frequency in Hz (for clicktrain, puretone, sawtooth)

"duration" is in seconds

will generate spatialized click trains in the processedWavs folder.  There will
be individual wav files for azimuth -90 to +90 degrees, with 0.1 degree
spacing, all at 0 degree elevation.
