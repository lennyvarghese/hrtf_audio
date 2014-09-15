"""
Hacky way to get csound to generate click train processed with HRTFs;
generates a temporary .csd file with some string mashing then uses a
system call to call csound

Requires:
    numpy
    scikits.audiolab
    csound (tested using 5.17 on Debian Wheezy, installed via repo)

usage:
    python binaural_stimuli.py TIMBRE DURATION [f0]

    TIMBRE is 'impulse', 'clicktrain', 'puretone', or 'sawtooth'
    DURATION is duration in seconds.
    f0 is the fundamental frequency for all timbres except impulse

note:
the .dat files are copies of the hrtf set included with csound
and were copied from /usr/share/csound/hrtf/hrtf-44100*.dat

For details on the origin of the hrtf files, see:
http://alumni.media.mit.edu/~kdm/hrtfdoc/section3_2.html
note: distance is 1.4 m

For details on the implementation of the hrtf interpolation, see:
http://www.csounds.com/manual/html/hrtfmove.html
http://www.csounds.com/journal/issue9/newHRTFOpcodes.html

LAV 2014-09-13
"""

import scikits.audiolab as audiolab
import numpy as np
import os
import errno
import sys
import make_waveforms
from scikits import audiolab

wavFileList = []

timbre = str(sys.argv[1])
dur = float(sys.argv[2])
if len(sys.argv) > 3:
    f0 = float(sys.argv[3])
else:
    f0 = ''

theTimbre = timbre.lower()
if theTimbre == 'sawtooth':
    audioOut = make_waveforms.sawtooth(dur + 1, f0, 44100)
elif theTimbre == 'puretone':
    audioOut = make_waveforms.puretone(dur + 1, f0, 44100)
elif theTimbre == 'clicktrain':
    audioOut = make_waveforms.clicktrain(dur + 1, f0, 44100)
elif theTimbre == 'impulse':
    audioOut = make_waveforms.click(dur+1, 44100)

audioOut = audioOut / max(abs(audioOut))

wavDir = 'processedWavs'
try:
    os.mkdir(wavDir)
except OSError, e:
    if e.errno == errno.EEXIST:
        pass

if f0:
    monoFilename = theTimbre + '{:.2f}'.format(f0).replace('.', 'p') + '.wav'
else:
    monoFilename = '{}.wav'.format(theTimbre)

audiolab.wavwrite(audioOut, os.path.join(wavDir, monoFilename), 44100)

# span -90 to 90 in 0.1 degree increments
# generate right side first
azimuthVal = np.linspace(0.0, 90.0, 901, endpoint=True)

for a in azimuthVal:
    if a > 0:
        aStr = 'pos' + '{:.1f}'.format(a).replace('.', 'p')
    else:
        aStr = '0'

    wavFileList.append(os.path.join(wavDir, aStr + '_' + monoFilename))

    tempFile = open('tempCSD_' + aStr + '.csd', 'w')
    tempFile.write('<CsoundSynthesizer>\n')
    tempFile.write('<CsOptions>\n')
    tempFile.write('-o ' + wavFileList[-1] + '\n')
    tempFile.write('</CsOptions>\n')
    tempFile.write('<CsInstruments>\n')
    tempFile.write('nchnls = 2\n')

    tempFile.write('instr 1\n')
    tempFile.write('ain soundin "' +
                   os.path.join(wavDir, monoFilename) +
                   '"\n')
    # calls hrtfmove in csound
    tempFile.write('aleft,aright hrtfmove ain, ')
    # with azimuth a degrees
    tempFile.write('{},'.format(a))
    # with elevation 0
    tempFile.write('0,')
    # interpolate using the hrtf data files specified below **
    tempFile.write('"hrtf-44100-left.dat","hrtf-44100-right.dat",')
    # with imode = 1 ("minimum phase")
    tempFile.write('1,')
    # with ifade = 1 ("low value recommended for complex sources")
    tempFile.write('1,')
    # with sampleRate 44100
    tempFile.write('44100\n')
    tempFile.write('outs    aleft, aright\n')
    tempFile.write('endin\n')
    tempFile.write('</CsInstruments>\n')
    tempFile.write('<CsScore>\n')
    tempFile.write('i1 0 ' + '{}'.format(dur) + '\n')
    tempFile.write('</CsScore>\n')
    tempFile.write('</CsoundSynthesizer>')

    tempFile.close()

    os.system('csound tempCSD_' + aStr + '.csd && ' +
              'rm tempCSD_' + aStr + '.csd')

maxVals = []
for x in wavFileList:
    audioData, _, _ = audiolab.wavread(x)
    maxVals.append(np.max(np.abs(audioData)))

scaler = max(maxVals) + 0.0000001

for x in wavFileList:
    audioData, fs, enc = audiolab.wavread(x)
    audiolab.wavwrite(audioData/scaler, x, fs, enc)

    # reverse to get left side
    if 'pos' in x:
        xsp = x.split('pos')
        y = xsp[0] + 'neg' + xsp[1]
        audiolab.wavwrite(np.fliplr(audioData/scaler), y, fs, enc)
