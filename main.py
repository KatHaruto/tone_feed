import pyaudio
import numpy as np
#import librosa


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
    #Fo_shift = 500
    #Fo = 400
    #n_steps = np.log2(Fo_shift / Fo)
    out = np.zeros((af.out_channels, af.CHUNK))
    out[1] = np.frombuffer(input_buff, dtype=np.int16)
    # out[0] = librosa.effects.pitch_shift(
    #    np.frombuffer(input_buff), 2048, n_steps=n_steps, bins_per_octave=1)
    out = np.reshape(out.T, (af.CHUNK * af.out_channels))
    out = out.astype(np.int16).tostring()
    return out


if __name__ == "__main__":
    # AudioFilterのインスタンスを作る場所
    af = AudioFilter()

    # ストリーミングを始める場所
    af.in_stream.start_stream()
    af.out_stream.start_stream()

    while af.in_stream.is_active() and af.out_stream.is_active():
        I = af.in_stream.read(af.CHUNK)
        out = toSpeaker(af, I)
        af.out_stream.write(out)

    # ストリーミングを止める場所
    af.in_stream.stop_stream()
    af.in_stream.close()
    af.out_stream.stop_stream()
    af.out_stream.close()
    af.close()
