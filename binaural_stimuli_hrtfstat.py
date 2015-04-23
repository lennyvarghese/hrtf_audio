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

from __future__ import print_function
import scikits.audiolab as audiolab
import numpy as np
import os
import errno
import sys
from audio_tools import *
from scikits import audiolab

wavFileList = []
Fs = 44100


''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                 CREATE SOUND FILE                  '
''''''''''''''''''''''''''''''''''''''''''''''''''''''

print("Generating Sound Files . . . \n\n")

timbre = str(sys.argv[1])
dur = float(sys.argv[2])
if len(sys.argv) > 3:
    f0 = float(sys.argv[3])
else:
    f0 = ''

#Get timbre
theTimbre = timbre.lower()
if theTimbre == 'sawtooth':
    audioOut = sawtooth(dur + 1, f0, Fs)
elif theTimbre == 'puretone':
    audioOut = puretone(dur + 1, f0, Fs)
elif theTimbre == 'clicktrain':
    audioOut = clicktrain(dur + 1, f0, Fs)
elif theTimbre == 'impulse':
    audioOut = impulse(dur+1, Fs)
elif theTimbre == 'noise':
    audioOut = noise(dur+1, Fs)

audioOut = audioOut / max(abs(audioOut))

# 'wav' file directory to save everything to
wavDir = 'processedWavs'

#Output Sound file
try:
    os.mkdir(wavDir)
except OSError, e:
    if e.errno == errno.EEXIST:
        pass

if f0:
    monoFilename = theTimbre + '{:.2f}'.format(f0).replace('.', 'p') + '.wav'
else:
    monoFilename = '{}.wav'.format(theTimbre)

audiolab.wavwrite(audioOut, os.path.join(wavDir, monoFilename), Fs)

# span -90 to 90 in 0.1 degree increments
azimuthVals = np.linspace(0.0, 90.0, 901, endpoint=True)

''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                  CSOUND HRTFSTAT                   '
''''''''''''''''''''''''''''''''''''''''''''''''''''''
print("Performing HRTFSTAT . . . \n\n")

CSoundCode = '''<CsoundSynthesizer>

			<CsOptions>
				-o %s
			</CsOptions>
			
			<CsInstruments>
				nchnls = 2
				instr 1
				ain soundin "%s"
				aleft,aright hrtfstat ain, %s, 0, "hrtf-44100-left.dat", "hrtf-44100-right.dat"
				outs    aleft, aright
				endin
			</CsInstruments>
    		           
			<CsScore>
				i1 0 %s
			</CsScore>
			
		</CsoundSynthesizer>
'''

    	
#Get sound input file
soundIn = os.path.join(wavDir, monoFilename);


for azimuth in azimuthVals:

	#Open temp file
	tempFile = open('tempCSD.csd', 'w')

	if azimuth > 0:
		aStr = 'pos' + '{:.1f}'.format(azimuth).replace('.', 'p')
	else:
		aStr = '0'

	#Get Filepath & append to 'wavFileList'
    	filepath = os.path.join(wavDir, aStr + '_' + monoFilename)
    	wavFileList.append(filepath)
	
	#Round azimuth
	az = round(azimuth,2)
	
	#Write to CSound Synthesizer
	inputCode = CSoundCode % (filepath, soundIn, az, dur)
	tempFile.write(inputCode)
	tempFile.close()
	os.system('csound tempCSD.csd')
	

# open everyhting just generated, and obtain the maximum value across all
# tokens and channels
maxVals = []
for x in wavFileList:
    audioData, _, _ = audiolab.wavread(x)
    maxVals.append(np.max(np.abs(audioData)))

scaler = max(maxVals) + 0.0000001

# scale everything so that the max value across the entire set of tokens is ~1.
# Also estimate the ITD and ILD from the stimuli and write these to a csv file.
outputInfo = open(os.path.join(wavDir, monoFilename.replace('.wav', '_info.csv')), 'w')

printStr = '{},{},{},{}\n'
outputInfo.write(printStr.format('filename', 'azimuth', 'itd', 'ild'))

for x in range(len(wavFileList)):

    audioData, fs, enc = audiolab.wavread(wavFileList[x])

    azimuth = azimuthVals[x]
    itdVal = get_itd(audioData, fs)
    ildVal = get_ild(audioData)

    audiolab.wavwrite(audioData/scaler, wavFileList[x], fs, enc)

    # reverse to get left side
    if 'pos' in wavFileList[x]:
        xsp = wavFileList[x].split('pos')
        leftFilename = xsp[0] + 'neg' + xsp[1]
        audiolab.wavwrite(np.fliplr(audioData/scaler), leftFilename, fs, enc)

    outputInfo.write(printStr.format(wavFileList[x], azimuth, itdVal, ildVal))

outputInfo.close()
