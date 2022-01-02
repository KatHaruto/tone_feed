from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
import os
import numpy as np
import pyworld as pw
import librosa
import pyrubberband as pyrb

template_dir = os.path.abspath("./src/templates")
app = Flask(__name__, template_folder=template_dir)
socketio = SocketIO(app, logger=True, engineio_logger=True)


@app.route("/")
def hello():
    return render_template("index.html")


@socketio.on("connect", namespace="/test")
def connect():
    pass


@socketio.on("wave", namespace="/test")
def event(data):
    signal = np.frombuffer(data, dtype=np.int16).astype(np.float64)
    _f0, t = pw.dio(signal, 44100)
    Fo = pw.stonemask(signal, _f0, t, 44100)
    Fo = Fo[Fo > 0]
    if len(Fo) > 0:
        note = librosa.hz_to_note(np.mean(Fo))
        print("data:", note)
        emit("note", {"note": note, "hz": np.mean(Fo)})
        Fo_shift = 440
        n_steps = np.log2(Fo_shift / Fo)
        emit(
            "pitch_shift", pyrb.pitch_shift(signal / 32768.0, 44100, n_steps) * 32768.0
        )


@socketio.event
def wave(data):
    emit("response", data)


@socketio.on("disconnect")
def disconnect_details():
    print("disconnected.")
    disconnect()


if __name__ == "__main__":
    socketio.run(app)
