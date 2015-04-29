"""
Hacky way to get csound to programmatically generate sounds with HRTFs;
generates a temporary .csd file with some string mashing then uses a system
call to call csound

Dependencise:
    numpy (tested using 1.9.2 via pip)
    scikits.audiolab (tested using 0.11.0 via pip)
    libsndfile (tested using 1.0.25-5 via Debian Wheezy repo; needed for
        scikits.audiolab)
    csound (tested using 5.17 on Debian Wheezy, installed via repo)
    audio_tools

usage:
    python make_binaural.py SAMPLERATE TIMBRE DURATION [f0] [headrad]

    SAMPLERATE: must be 44100, 48000, 96000
    TIMBRE: impulse, click, clicktrain, puretone, or sawtooth
    DURATION: duration in seconds. For clicks and impulses, this defines the
        total length of the wav file and not the clicks themselves. The clicks
        are always 80 microseconds in duration. When "impulse" is selected, a
        single sample is set to 1 (i.e., 1/Fs in duration).
    f0, required for sawtooth, clicktrain, puretone; the fundamental
        frequency for all timbres except impulse/click. Specify as 0 for click
        and impulse if the next argument is necessary, otherwise omit.
    headrad, optional, specify head radius in cm for interpolation (defaults to
        9 cm, same as csound)

note:
the .dat files are copies of the hrtf set included with csound and were copied
from /usr/share/csound/hrtf/hrtf-*.dat. The distance on these files is always
1.4m.

For details on the origin of the hrtf files, see:
    http://alumni.media.mit.edu/~kdm/hrtfdoc/section3_2.html
    http://sound.media.mit.edu/resources/KEMAR.html

Additional references (should be cited when this is used):
    http://sound.media.mit.edu/resources/KEMAR/hrtfdoc.ps
    http://www.csounds.com/manual/html/hrtfmove.html

Last updated: LAV 2015-04-28
"""

from __future__ import print_function
from scikits import audiolab
import audio_tools
import numpy as np
import os
import errno
import sys

wavFileList = []


''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                 CREATE MONO AUDIO                  '
''''''''''''''''''''''''''''''''''''''''''''''''''''''

print("Generating Sound Files . . . \n\n")
Fs = int(sys.argv[1])
theTimbre = str(sys.argv[2]).lower()
dur = float(sys.argv[3])
try:
    f0 = float(sys.argv[4])
except IndexError:
    f0 = 0.0

try:
    headRad = float(sys.argv[5])
except IndexError:
    headRad = 9.0

if not (Fs == 48000 or Fs == 44100 or Fs == 96000):
    raise ValueError('Fs must be 44100, 48000, or 96000')

if (theTimbre in ['sawtooth', 'puretone', 'clicktrain']) and f0 == 0.0:
    raise ValueError('F0 must be specified for clicktrain, puretone, sawtooth')

# Get timbre
if theTimbre == 'sawtooth':
    audioOut = audio_tools.sawtooth(dur, f0, Fs)
elif theTimbre == 'puretone':
    audioOut = audio_tools.puretone(dur, f0, Fs)
elif theTimbre == 'clicktrain':
    audioOut = audio_tools.clicktrain(dur, f0, Fs)
elif theTimbre == 'impulse':
    audioOut = audio_tools.impulse(dur, Fs)
elif theTimbre == 'click':
    audioOut = audio_tools.click(dur, Fs)

audioOut = audioOut / max(abs(audioOut))

radStr = '{:.2f}'.format(headRad).replace('.', 'p')
f0Str = '{:.2f}'.format(f0).replace('.', 'p')
durStr = '{:.2f}'.format(1000*dur).replace('.', 'p')

# wav file directory to save everything to
if f0:
    wavDir = 'output/{:d}_{:s}_dur{:s}ms_rad{:s}cm_f0{:s}'.format(Fs,
                                                                  theTimbre,
                                                                  durStr,
                                                                  radStr,
                                                                  f0Str)
else:
    wavDir = 'output/{:d}_{:s}_dur{:s}ms_rad{:s}cm'.format(Fs,
                                                           theTimbre,
                                                           durStr,
                                                           radStr)

# Output Sound file
try:
    os.mkdir('output')
except OSError, e:
    if e.errno == errno.EEXIST:
        pass

try:
    os.mkdir(wavDir)
except OSError, e:
    if e.errno == errno.EEXIST:
        pass

monoFilename = 'original.wav'

# save as 32-bit float wav file
audiolab.wavwrite(audioOut,
                  os.path.join(wavDir, monoFilename),
                  Fs,
                  enc='float32')


''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                  CSOUND HRTFSTAT                   '
''''''''''''''''''''''''''''''''''''''''''''''''''''''
# span 0 to 180 in 0.1 degree increments
azimuthVals = np.linspace(0.0, 180, 1801, endpoint=True)

print("Calling cSound...\n\n")

CSoundCode = '''
<CsoundSynthesizer>
    <CsOptions>
        -o {0:s} -W -f
    </CsOptions>

    <CsInstruments>
        sr = {1:d}
        ksmps = 10
        nchnls = 2
        instr 1
        ain soundin "{2:s}"
        aleft,aright hrtfstat ain, {3:f}, 0, "hrtf/hrtf-{1:d}-left.dat", "hrtf/hrtf-{1:d}-right.dat", {4:f}, {1:d}
        outs    aleft, aright
        endin
    </CsInstruments>

    <CsScore>
        i1 0 {5:f}
    </CsScore>
</CsoundSynthesizer>
'''

# Get sound input file
soundIn = os.path.join(wavDir, monoFilename)

for azimuth in azimuthVals:

    # Open temp file
    tempFile = open('.tempCSD.csd', 'w')

    if azimuth > 0 and azimuth < 180:
        aStr = 'pos' + '{:.1f}'.format(azimuth).replace('.', 'p')
    elif azimuth == 0:
        aStr = '0'
    elif azimuth == 180:
        aStr = '180'

    # Get Filepath & append to 'wavFileList'
    filepath = os.path.join(wavDir, aStr + '.wav')
    wavFileList.append(filepath)

    # Write to CSound Synthesizer
    inputCode = CSoundCode.format(filepath, Fs, soundIn,
                                  azimuth, headRad, dur)
    tempFile.write(inputCode)
    tempFile.close()
    os.system('csound .tempCSD.csd')

os.remove('.tempCSD.csd')


''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                  STIMULUS RESCALING                '
''''''''''''''''''''''''''''''''''''''''''''''''''''''

# open everyhting just generated, and obtain the maximum value across all
# tokens and channels
maxVals = []
for x in wavFileList:
    audioData, _, _ = audiolab.wavread(x)
    maxVals.append(np.max(np.abs(audioData)))

scaler = max(maxVals) + 1E-16

# scale everything so that the max value across the entire set of tokens is ~1.
# Also estimate the ITD and ILD from the stimuli and write these to a csv file.
outputInfo = open(os.path.join(wavDir, 'info.csv'), 'w')

printStr = '{},{},{},{}\n'
outputInfo.write(printStr.format('filename', 'azimuth (deg)',
                                 'itd (s)', 'ild (dB)'))
printStr = '{:s},{:.1f},{:E},{:E}\n'

for x in range(len(wavFileList)):

    audioData, fs, enc = audiolab.wavread(wavFileList[x])

    azimuth = azimuthVals[x]
    itdVal = audio_tools.get_itd(audioData, fs)
    ildVal = audio_tools.get_ild(audioData)

    audiolab.wavwrite(audioData/scaler, wavFileList[x], fs, enc)

    # reverse to get left side; see Gardner/Martin technical note for why this
    # makes sense
    if 'pos' in wavFileList[x]:
        xsp = wavFileList[x].split('pos')
        leftFilename = xsp[0] + 'neg' + xsp[1]
        audiolab.wavwrite(np.fliplr(audioData/scaler), leftFilename, fs, enc)

    outputInfo.write(printStr.format(wavFileList[x], azimuth, itdVal, ildVal))

outputInfo.close()
