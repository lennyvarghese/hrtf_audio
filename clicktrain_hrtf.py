"""
Hacky way to get csound to generate click train processed with HRTFs;
generates a temporary .csd file with some string mashing then uses a
system call to call csound

Requires:
    numpy
    scikits.audiolab
    csound (tested using 5.17 on Debian Wheezy, installed via repo)

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
from make_audio_samples import clicktrain

if __name__ == '__main__':

    f0 = float(sys.argv[1])
    dur = float(sys.argv[2])

    clickTrainOut = clicktrain(dur+1, f0, 44100)
    clickTrainOut = clickTrainOut / max(abs(clickTrainOut))

    wavDir = 'processedWavs'
    try:
        os.mkdir(wavDir)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass

    monoFilename = ('clicktrain_' +
                    ('{}'.format(f0)).replace('.', 'p') +
                    'Hz.wav')
    audiolab.wavwrite(clickTrainOut, os.path.join(wavDir, monoFilename), 44100)

    # span -90 to 90 in 0.1 degree increments
    azimuthVal = np.arange(-90., 90., 0.1)

    for a in azimuthVal:

        if a < 0:
            aStr = '{:.1f}'.format(a).replace('.', 'p').replace('-', 'neg')
        elif a > 0:
            aStr = 'pos' + '{:.1f}'.format(a).replace('.', 'p')
        else:
            aStr = 'center'

        tempFile = open('tempCSD_' + aStr + '.csd', 'w')
        tempFile.write('<CsoundSynthesizer>\n')
        tempFile.write('<CsOptions>\n')
        tempFile.write('-o ' +
                       os.path.join(wavDir, aStr + '_' + monoFilename) +
                       '\n')
        tempFile.write('</CsOptions>\n')
        tempFile.write('<CsInstruments>\n')
        tempFile.write('nchnls = 2\n')

        tempFile.write('instr 1\n')
        tempFile.write('ain soundin "' + os.path.join(wavDir, monoFilename) + '"\n')
        # calls hrtfmove in csound
        tempFile.write('aleft,aright hrtfmove ain, ')
        # with azimuth a
        tempFile.write('{:.4f}'.format(a))
        # with elevation 0
        # interpolate using the hrtf data files specified below **
        # with imode = 1 ("minimum phase")
        # with ifade = 1 ("low value recommended for complex sources")

        tempFile.write(',0,"hrtf-44100-left.dat","hrtf-44100-right.dat",' +
                       '1,1,44100\n')
        tempFile.write('outs    aleft, aright\n')
        tempFile.write('endin\n')
        tempFile.write('</CsInstruments>\n')
        tempFile.write('<CsScore>\n')
        tempFile.write('i1 0 ' + '{:.4f}'.format(dur) + '\n')
        tempFile.write('</CsScore>\n')
        tempFile.write('</CsoundSynthesizer>')

        tempFile.close()

        os.system('csound tempCSD_' + aStr + '.csd && ' +
                  'rm tempCSD_' + aStr + '.csd')
