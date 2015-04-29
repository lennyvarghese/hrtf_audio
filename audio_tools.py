import numpy as np
from scipy import signal

SAMPLERATE = 44100
DURATION = 1.000
F0 = 107.


def clicktrain(duration=DURATION, f0=F0, sampleRate=SAMPLERATE):
    '''
    Generate an alternatinv polarity click train.

    duration: length in seconds (default: 1 s)

    f0: fundamental frequency (determines impulse spacing; default: 107 Hz)

    sampleRate: the desired samplerate (default: 44100)
    '''

    t = np.linspace(0.0, duration, duration*sampleRate, endpoint=False)

    audioOut = np.zeros(t.shape, dtype=np.float)

    clickSpacingSamples = int(sampleRate / f0)

    clickSamples = np.arange(0, t.shape[0], clickSpacingSamples)
    polarities = np.zeros(clickSamples.shape, dtype=float)
    polarities[0::2] = 1.0
    polarities[1::2] = -1.0

    audioOut[clickSamples] = polarities

    nSamplesHigh = int(np.round(80E-6*sampleRate))
    for y in range(nSamplesHigh):
        audioOut[clickSamples+y] = audioOut[clickSamples]

    return scale_rms(audioOut)


def impulse(duration=DURATION, sampleRate=SAMPLERATE):
    '''
    Generate a single impulse (x = 1) at t = 0, with zeros afterwards specified
    by duration
    '''

    x = np.zeros(duration*sampleRate, dtype=float)

    x[0] = 1.0

    return x


def click(duration=DURATION, sampleRate=SAMPLERATE):
    '''
    Generate a single 80 us click (x = 1) at t = 0
    '''

    x = np.zeros(duration*sampleRate, dtype=float)

    nSamplesHigh = int(np.round(80E-6*sampleRate))
    for y in range(nSamplesHigh):
        x[y] = 1.0

    return x


def sawtooth(duration=DURATION, f0=F0, sampleRate=SAMPLERATE, N=64):
    '''
    Generate a sawtooth wave.

    duration: length in seconds (default: 1 s)

    f0: fundamental frequency (determines impulse spacing; default: 107 Hz)

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

    f0: fundamental frequency (determines impulse spacing; default: 107 Hz)

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

    q = fftcorrelate(rightSignal, leftSignal)

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


def nextpow2(value):
    '''
    Computes X >= input, such that log2(X) is an integer.
    '''
    return int(2**np.ceil(np.log2(value)))


def fftconvolve(x, b, nfft=None):
    '''
    1D convolution using FFT
    '''
    if nfft is None:
        nfft = nextpow2(len(x) + len(b) - 1)

    result = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(b, nfft), nfft)

    return result[0:(x+b)]


def fftcorrelate(x1, x2=None, meanSubtract=False):
    '''
    1D auto/cross correlation using FFT
    '''
    if not isinstance(x1, np.ndarray):
        x1 = np.array(x1)

    if meanSubtract:
        x1 = x1 - x1.mean()

    if np.any(x2):
        if not isinstance(x2, np.ndarray):
            x2 = np.array(x2)

        if meanSubtract:
            x2 = x2 - x2.mean()

        nSamps = x1.shape[0] + x2.shape[0] - 1
        nfft = nextpow2(nSamps)
        X1 = np.fft.rfft(x1, nfft)
        X2 = np.fft.rfft(x2, nfft)
        toRoll = x2.shape[0] - 1
    else:
        nSamps = 2*x1.shape[0] - 1
        nfft = nextpow2(nSamps)
        X1 = np.fft.rfft(x1, nfft)
        X2 = X1
        toRoll = x1.shape[0] - 1

    result = np.fft.irfft(X1 * np.conjugate(X2), nfft)

    return np.roll(result, toRoll)[0:nSamps]


def vocoder(inputData, f0=F0, sampleRate=SAMPLERATE, nBands=64):
    '''
    Performs click-train vocoding on an input stimulus. Input signal is
    full-wave rectified and band-pass filtered to obtain the local envelope,
    then each envelope is multiplied by a click train. The result is passed
    back through the bandpass filter, and the results across bands summed to
    get the output.

    Each click is 80 uSeconds. First filter corner frequency for high-pass is
    500 Hz. Corner frequency for low-pass on last filter is 200 Hz below
    Nyquist.

    inputData: monaural stimulus to be vocoded

    f0: fundamental frequency (determines impulse spacing; default: 107 Hz)

    sampleRate: the desired samplerate (default: 44100)

    nBands: number of vocoding bands (bandpass filters) to use (default: 64)
    '''

    if not isinstance(inputData, np.ndarray):
        inputData = np.ndarray(inputData)

        if len(inputData.shape) > 1:
            raise ValueError('only 1 channel audio is supported.')

    nyquist = sampleRate / 2.0

    # generate the click kernel
    clickSamples = np.ceil(sampleRate * 0.00008)
    clickSpacing = np.round(1.0/f0 * float(sampleRate))

    # envelope filter
    nTapsEnv = 0
    transition = 50. / nyquist
    while nTapsEnv % 2 != 1:
        nTapsEnv, betaEnv = signal.kaiserord(100.0, transition)
        transition = transition * 1.01
    envFilter = signal.firwin(nTapsEnv, 20. / nyquist,
                              window=('kaiser', betaEnv),
                              pass_zero=True)

    # vocoding filters
    maxLen = envFilter.shape[0]

    fc = (np.logspace(np.log10(500),
                      np.log10(sampleRate/2.0 - 200),
                      nBands+1) / nyquist)
    b = []
    for z in range(len(fc)-1):
        nTaps = 0
        transition = (fc[z+1] - fc[z])
        while nTaps % 2 != 1:
            nTaps, beta = signal.kaiserord(60.0, transition)
            transition = transition * 1.01

        b.append(signal.firwin(nTaps, [fc[z], fc[z+1]],
                               window=('kaiser', beta),
                               pass_zero=False))
        if b[-1].shape[0] > maxLen:
            maxLen = b[-1].shape[0]

    nfft = nextpow2(inputData.shape[0] + 2*maxLen - 1)

    output = []
    portionLengths = []
    # time for some action
    for f in range(len(b)):
        # filter the samples with appropriate bandpass
        grpDelay1 = (len(b[f]) - 1) / 2
        rectResult = fftconvolve(inputData, b[f], nfft)[grpDelay1:]**2.0

        # filter the samples with envelope filter
        grpDelay2 = (len(envFilter) - 1) / 2
        envelope = np.abs(fftconvolve(rectResult, envFilter, nfft)[grpDelay2:])

        clickTrain = np.zeros(envelope.shape)
        clickTrainStarts = np.arange(0, clickTrain.shape[0], int(clickSpacing))
        clickTrainEnds = clickTrainStarts + clickSamples

        # generate the alternating polarity click train
        for n in range(len(clickTrainStarts)):
            if n % 2 == 1:
                clickTrain[clickTrainStarts[n]:clickTrainEnds[n]] = 1.0
            else:
                clickTrain[clickTrainStarts[n]:clickTrainEnds[n]] = -1.0

        # pass result back through bandpass filter
        finalResult = fftconvolve(envelope*clickTrain, b[f], nfft)[grpDelay1:]

        output.append(finalResult)
        portionLengths.append(output[-1].shape[0])

    maxPortionLength = max(portionLengths)
    for y in range(len(output)):
        output[y] = np.pad(output[y],
                           ((0, maxPortionLength - output[y].shape[0])),
                           'constant')

    output = np.sum(np.array(output), axis=0)

    output /= np.max(output)

    return output
