from multiprocessing import Process
import threading
import time
import pyaudio
import numpy as np
import librosa
from math import log10
import pyworld as pw
import scipy
import pyrubberband as pyrb
from collections import deque

from sample import RATE


def audio_filter():

    p = pyaudio.PyAudio()
    rate = 16000  # 一秒間のサンプリング回数
    CHUNK = 1024  # 何サンプルで一つのデータとするか
    format = pyaudio.paInt16
    input_queue = deque(maxlen=CHUNK)
    output_queue = deque(maxlen=CHUNK*2)

    def recorder():
        in_stream = p.open(
            format=format,
            channels=1,
            rate=rate,
            frames_per_buffer=CHUNK,
            input=True,
            output=False
        )

        while in_stream.is_active():
            data = in_stream.read(CHUNK)
            # len(data) -> 2048 (バイト形式のため)
            # len(np.frombuffer(data, dtype=np.int16)) -> 1024 == CHUNK
            input_queue.extend(np.frombuffer(data, dtype=np.int16))

    def pitch(signal):
        out_channels = 2
        out = np.zeros((out_channels, len(signal)))
        if max(signal) > 0 and 20*log10(max(signal)) > 60:
           # Fo, voiced_flag, voiced_prpb = librosa.pyin(
            #    signal, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            # librosa.pyin() リアルタイム性で断念
            _f0, t = pw.dio(signal, rate)
            Fo = pw.stonemask(signal, _f0, t, rate)
            Fo = np.mean(Fo)
            Fo_shift = 440
            if Fo != 0:
                n_steps = np.log2(Fo_shift / Fo)
                out[0] = pyrb.pitch_shift(
                    signal / 32768.0, rate, n_steps) * 32768.0
        out[1] = signal
        out = np.reshape(out.T, (len(signal) * out_channels))
        # out = out.astype(np.int16).tobytes()

        return out

    def converter():

        prev_input = np.zeros(CHUNK, dtype=np.int16)
        prev_output = np.zeros(CHUNK*2, dtype=np.int16)
        window = scipy.signal.get_window('hann', CHUNK * 2, fftbins=True)
        while True:
            if not len(input_queue):
                time.sleep(0.01)
                continue
            data = np.array(input_queue, dtype='int16').astype(np.float64)
            # len(input_queue) -> 1024
            # len(data) -> 1024
            input_queue.clear()

            input_signal = np.concatenate((prev_input, data))
            # len(input_signal) -> 2048 == CHUNK*2
            prev_input = data
            output_signal = pitch(input_signal * window).astype(np.int16)
            # len(output_signal) -> 4096
            output_queue.extend(prev_output + output_signal[:CHUNK*2])
            prev_output = output_signal[CHUNK*2:]

    def player():
        out_stream = p.open(
            format=format,
            channels=2,
            frames_per_buffer=CHUNK,
            rate=rate,
            input=False,
            output=True
        )
        while True:
            if not len(output_queue):
                time.sleep(0.01)
                continue
            data = np.array(output_queue, dtype=np.int16)
            # len(output_queue) -> 1024
            # len(data)->1024
            output_queue.clear()
            out_stream.write(data.tobytes())

    th_record = threading.Thread(target=recorder)
    th_convert = threading.Thread(target=converter)
    th_play = threading.Thread(target=player)

    th_record.start()
    th_convert.start()
    th_play.start()


if __name__ == "__main__":
    # AudioFilterのインスタンスを作る場所
    audio_process = Process(target=audio_filter)

    try:
        audio_process.start()
    except KeyboardInterrupt:
        print('\nInterrupt!')
