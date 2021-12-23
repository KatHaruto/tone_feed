from multiprocessing import Process
import threading
import time
from math import log10
from collections import deque
from librosa.util.exceptions import ParameterError
from numpy import lib
import pyaudio
import numpy as np
import argparse
import librosa
import pyworld as pw
from scipy.signal import get_window
import pyrubberband as pyrb


#from concurrent.futures import ThreadPoolExecutor


def audio_filter(Fo_shift):

    p = pyaudio.PyAudio()

    rate = 16000  # 一秒間のサンプリング回数
    CHUNK = 1024  # 何サンプルで一つのデータとするか
    FORMAT = pyaudio.paInt16
    input_queue = deque(maxlen=CHUNK)
    output_queue = deque(maxlen=CHUNK*2)  # 2チャンネル

    def recorder():
        in_stream = p.open(
            format=FORMAT,
            channels=1,
            rate=rate,
            frames_per_buffer=CHUNK,
            input=True,
            output=False
        )

        while in_stream.is_active():
            data = in_stream.read(CHUNK)
            # len(data) -> 2048 (なぜ？バイト形式のため?)
            # len(np.frombuffer(data, dtype=np.int16)) -> 1024 == CHUNKとなるように
            input_queue.extend(np.frombuffer(data, dtype=np.int16))

    def pitch(signal):
        out_channels = 2
        out = np.zeros((out_channels, len(signal)))
        if Fo_shift and max(signal) > 0 and 20*log10(max(signal)) > 60:
            # Fo, voiced_flag, voiced_prpb = librosa.pyin(
            #    signal, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            # librosa.pyin() リアルタイム性で断念
            _f0, t = pw.dio(signal, rate)
            Fo = pw.stonemask(signal, _f0, t, rate)
            Fo = Fo[Fo > 0]
            if len(Fo) > 0:
                Fo = Fo[0]
                # print(librosa.hz_to_note(Fo))
                n_steps = np.log2(Fo_shift / Fo)
                #pitch_shift: 正規化して帰ってくる
                # signalは符号付き16ビット配列のため-32768~32767の値となっているはず
                out[0] = pyrb.pitch_shift(
                    signal / 32768.0, rate, n_steps) * 32768.0
        out[1] = signal
        out = np.reshape(out.T, (len(signal) * out_channels))
        # 出力チャンネルを1,2とし、データを1[0],1[1],1[2]...などとすると
        # out -> [1[0],2[0],1[1],2[1],1[2],...]のような並び

        return out

    def converter():

        prev_input = np.zeros(CHUNK, dtype=np.int16)
        prev_output = np.zeros(CHUNK*2, dtype=np.int16)
        window = get_window('hann', CHUNK * 2, fftbins=True)
        while True:
            if len(input_queue) == 0:
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
            format=FORMAT,
            channels=2,
            frames_per_buffer=CHUNK,
            rate=rate,
            input=False,
            output=True
        )
        while True:
            if len(output_queue) == 0:
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

    '''with ThreadPoolExecutor(max_workers=4) as executor:
        executor.submit(recorder)
        executor.submit(converter)
        executor.submit(player)'''


if __name__ == "__main__":
    # AudioFilterのインスタンスを作る場所
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pitch')
    args = parser.parse_args()
    try:
        if args.pitch:
            Fo_shift = librosa.note_to_hz(args.pitch)
    except ParameterError as e:
        print(e)
        exit()
    audio_process = Process(target=audio_filter, args=(Fo_shift,))
    audio_process.start()
