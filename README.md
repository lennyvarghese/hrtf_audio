hrtf_audio
==========

Hacky way to get csound to programmatically generate sounds with HRTFs;
generates a temporary .csd file with some string mashing then uses a system
call to call csound

Dependencies
-------------
  * numpy (tested using 1.9.2 via pip)

  * scikits.audiolab (tested using 0.11.0 via pip)

  * libsndfile (tested using 1.0.25-5 via Debian Wheezy repo; needed for
    scikits.audiolab)

  * csound (tested using 5.17 on Debian Wheezy, installed via repo)

  * audio_tools

Usage
-------------
```python make_binaural.py SAMPLERATE TIMBRE DURATION [f0] [headrad] [wav]```

SAMPLERATE: must be 44100, 48000, 96000

TIMBRE: impulse, click, clicktrain, puretone, sawtooth, or custom. If
    custom, the last argument must be specified and point to the wav file
    to be interpolated.

DURATION: duration in seconds. For clicks and impulses, this defines the
    total length of the wav file and not the clicks themselves. The clicks
    are always 80 microseconds in duration. When "impulse" is selected, a
    single sample is set to 1 (i.e., 1/Fs in duration). Set to 0 if using
    "custom", as this will be ignored.

f0, required for sawtooth, clicktrain, puretone; the fundamental
    frequency for all timbres except impulse/click. Specify as 0 for click
    and impulse if the next argument is necessary, otherwise omit.

headrad, optional, specify head radius in cm for interpolation (defaults to
    9 cm, same as csound)

wav, required if timbre=custom. Path to a wav file to be interpolated.

Notes:
----------

the .dat files are copies of the hrtf set included with csound and were copied
from /usr/share/csound/hrtf/hrtf-*.dat. The distance on these files is always
1.4m.

For details on the origin of the hrtf files, see:

  * http://alumni.media.mit.edu/~kdm/hrtfdoc/section3_2.html

  * http://sound.media.mit.edu/resources/KEMAR.html

Additional references (should be cited when this is used):

  * http://sound.media.mit.edu/resources/KEMAR/hrtfdoc.ps

  * http://www.csounds.com/manual/html/hrtfmove.html
