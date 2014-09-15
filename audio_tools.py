import numpy as np
from scipy import signal

SAMPLERATE = 44100
DURATION = 0.100
F0 = 100.


def clicktrain(duration=DURATION, f0=F0, sampleRate=SAMPLERATE):
    '''
    Generate a click train.

    duration: length in seconds (default: 1 s)

    f0: fundamental frequency (determines impulse spacing; default: 100 Hz)

    sampleRate: the desired samplerate (default: 44100)
    '''

    t = np.linspace(0.0, duration, duration*sampleRate, endpoint=False)

    audioOut = np.zeros(t.shape, dtype=np.float)

    clickSpacingSamples = int(sampleRate / f0)

    clickSamples = range(0, t.shape[0], clickSpacingSamples)
    audioOut[clickSamples] = 1.0

    return scale_rms(audioOut)


def impulse(duration=DURATION, sampleRate=SAMPLERATE):
    '''
    Generate a single impulse (x = 1) at t = 0, with zeros afterwards specified
    by duration
    '''

    x = np.zeros(duration*sampleRate, dtype=float)

    x[0] = 1.0

    return x


def sawtooth(duration=DURATION, f0=F0, sampleRate=SAMPLERATE, N=64):
    '''
    Generate a sawtooth wave.

    duration: length in seconds (default: 1 s)

    f0: fundamental frequency (determines impulse spacing; default: 100 Hz)

    sampleRate: the desired samplerate (default: 44100)

    N: number of sinusoids to sum (default: 64)
    '''

    t = np.linspace(0.0, duration, duration*sampleRate, endpoint=False)

    audioOut = np.zeros(t.shape, dtype=np.float)

    for k in range(1, N+1):
        audioOut += (np.sin(2*np.pi*k*f0*t) / k)

    return scale_rms(audioOut)


def puretone(duration=DURATION, f0=F0, sampleRate=SAMPLERATE):
    '''
    Generate a pure tone.

    duration: length in seconds (default: 1 s)

    f0: fundamental frequency (determines impulse spacing; default: 113 Hz)

    sampleRate: the desired samplerate (default: 44100)
    '''

    t = np.linspace(0.0, duration, duration*sampleRate, endpoint=False)

    audioOut = np.sin(2*np.pi*f0*t)

    return scale_rms(audioOut)


def scale_rms(audio):
    """
    scales audio samples so that entire sample RMS = 1

    you don't really want to do this if nchan > 1

    """
    return audio / get_rms(audio)


def get_rms(audio):
    """
    computes rms down the first axis
    """

    return np.sqrt((audio ** 2.0).mean(axis=0))


# binaural functions


def get_itd(audioInput, sampleRate, normalize=False):

    '''
    computes itd by cross-correlating left and right channels.
    negative lag indicates left-ear leads
    '''

    assert audioInput.shape[1] == 2

    leftSignal = audioInput[:, 0]
    rightSignal = audioInput[:, 1]

    if normalize:
        leftSignal = scale_rms(leftSignal)
        rightSignal = scale_rms(rightSignal)

    q = signal.correlate(rightSignal, leftSignal, 'full')

    lagSamples = len(q) - len(rightSignal) - np.argmax(q)

    return lagSamples / float(sampleRate)


def get_ild(audioInput):
    '''
    computes ild
    returns ild in db (right signal relative to left signal)
    '''
    assert audioInput.shape[1] == 2

    leftSignal = audioInput[:, 0]
    rightSignal = audioInput[:, 1]

    leftSignalRMS = get_rms(leftSignal)
    rightSignalRMS = get_rms(rightSignal)

    return 20*np.log10(rightSignalRMS/leftSignalRMS)
