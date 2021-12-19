import pyaudio
import numpy as np
import librosa
from math import log10
import pyrubberband as pyrb


class AudioFilter:
    def __init__(self):
        # オーディオに関する設定
        self.p = pyaudio.PyAudio()
        self.in_channels = 1
        self.out_channels = 2
        self.rate = 44100  # DVDレベルなので重かったら16000にする
        self.CHUNK = 1024
        self.format = pyaudio.paInt16
        self.in_stream = self.p.open(
            format=self.format,
            channels=self.in_channels,
            rate=self.rate,
            frames_per_buffer=self.CHUNK,
            input=True
        )
        self.out_stream = self.p.open(
            format=self.format,
            channels=self.out_channels,
            rate=self.rate,
            frames_per_buffer=self.CHUNK,
            output=True
        )

    def close(self):
        self.p.terminate()


def toSpeaker(af, input_buff):
    out = np.zeros((af.out_channels, af.CHUNK))
    input_data = np.frombuffer(input_buff, dtype=np.int16).astype(np.float64)

    # Fo, voiced_flag, voiced_prpb = librosa.pyin(input_data, fmin=librosa.note_to_hz(
    #    'C2'), fmax=librosa.note_to_hz('C7'))
    # if voiced_flag.any():
    if 20*log10(max(input_data)) > 60:
        #print(Fo, voiced_flag)
        Fo_shift = 500
        #Fo = np.mean(Fo[voiced_flag])
        Fo = 400
        n_steps = np.log2(Fo_shift / Fo)
        out[0] = pyrb.pitch_shift(
            input_data / 32768.0, 2048, 3)*32768.0
        # out[0] = librosa.effects.pitch_shift(
        #    input_data, 2048, n_steps=n_steps, bins_per_octave=1)
    out[1] = input_data
    out = np.reshape(out.T, (af.CHUNK * af.out_channels))
    out = out.astype(np.int16).tobytes()

    return out


if __name__ == "__main__":
    # AudioFilterのインスタンスを作る場所
    af = AudioFilter()

    # ストリーミングを始める場所
    af.in_stream.start_stream()
    af.out_stream.start_stream()
    try:
        while af.in_stream.is_active() and af.out_stream.is_active():
            I = af.in_stream.read(af.CHUNK, exception_on_overflow=False)
            out = toSpeaker(af, I)
            af.out_stream.write(out)
    except KeyboardInterrupt:
        print('\nInterrupt')
    finally:
        # ストリーミングを止める場所
        af.in_stream.stop_stream()
        af.in_stream.close()
        af.out_stream.stop_stream()
        af.out_stream.close()
        af.close()
