// Copyright (c) 2019 ml5
//
// This software is released under the MIT License.
// https://opensource.org/licenses/MIT

/* ===
ml5 Example
Basic Pitch Detection
=== */

let audioContext;
let mic;
let pitch;
const width = document.documentElement.clientWidth;
//const height = document.documentElement.clientHeight;
const height = 500;
let point_list = [];
const point_num = 10;
const point_size = 3;
const freqs = new Array(12);
let targetNote;
let closest;
let base_c = 130.813;
let canvas;
let ctx;
let freq = -1;
let shifter;
let splitter;
let merger;
const notes = [
  "C",
  "C#",
  "D",
  "D#",
  "E",
  "F",
  "F#",
  "G",
  "G#",
  "A",
  "A#",
  "B",
  "C",
];
function setup() {
  initializeCanvas();
  targetNote = document.getElementById("target").value;
  freqs[0] = [32.703, 65.406, 130.813, 261.626, 523.251, 1046.502];
  for (let i = 1; i < freqs.length; i++) {
    freqs[i] = freqs[0].map((v) => v * Math.pow(2, i / 12));
  }
  mic = new p5.AudioIn();
  mic2 = mic;
  mic.start();
}

const initializeCanvas = () => {
  canvas = document.getElementById("myChart");
  canvas.width = width;
  canvas.height = height + 20;
  ctx = canvas.getContext("2d");
  ctx.lineWidth = 10;
  ctx.strokeStyle = "#FF0000";
  ctx.lineCap = "round";
};

function touchStarted() {
  userStartAudio();
  getAudioContext().suspend();
  if (getAudioContext().state !== "running") {
    //audioContext = getAudioContext();
    audioContext = getAudioContext();
    audioContext.resume();
    Tone.context = audioContext;

    // ここから本格スタート
    startPitch();
    shifter = new Tone.PitchShift({
      pitch: 0,
    });
    merger = audioContext.createChannelMerger(2);
    mic.connect(merger, 0, 0);
    mic.connect(shifter);
    shifter.connect(merger, 0, 1);
    merger.connect(audioContext.destination);
  }
}
const startPitch = () => {
  pitch = ml5.pitchDetection("./model/", audioContext, mic.stream, modelLoaded);
};
const modelLoaded = () => {
  select("#status").html("Model Loaded");
  getPitch();
};

const getPitch = () => {
  pitch.getPitch((err, frequency) => {
    if (frequency) {
      select("#result").html(frequency);
      freq = frequency;
    } else {
      select("#result").html("No pitch detected");
      freq = -1;
    }
    getPitch();
  });
};
const onChangeTarget = () => {
  targetNote = document.getElementById("target").value;
};
function drawnotes() {
  notes.map((note, i) => {
    ctx.fillText(note, 0, 15 + height * (2 - Math.pow(2, i / 12)));
    ctx.beginPath();
    ctx.moveTo(15, 10 + height * (2 - Math.pow(2, i / 12)));
    ctx.lineTo(width, 10 + height * (2 - Math.pow(2, i / 12)));
    if (i == targetNote || (targetNote == 0 && (i == 0 || i == 12))) {
      ctx.strokeStyle = "#00FF00";
    } else if ([1, 3, 6, 8, 10].includes(i)) {
      ctx.strokeStyle = "#C0C0C0";
    } else {
      ctx.strokeStyle = "#000000";
    }
    ctx.lineWidth = 5;
    ctx.stroke();
  });
}
function drawPoint(x, y) {
  ctx.beginPath();
  ctx.arc(x, y, point_size, (0 * Math.PI) / 180, (360 * Math.PI) / 180, false);
  ctx.fillStyle = "rgb(255,0,0)";
  ctx.fill();
  ctx.restore();
}

const drawAllPoints = () => {
  point_list.map((p, i) => {
    drawPoint(
      width / 2 - (width / 2 / point_num) * (point_list.length - i),
      7.5 + p
    );
  });
};
function draw() {
  ctx.clearRect(0, 0, width, height + 20);
  drawnotes();
  if (point_list.length > point_num) {
    point_list.shift();
  }
  if (freq < 0) {
    drawAllPoints();
    return;
  }
  base_c = freqs[0].filter((e) => e <= freq).slice(-1)[0];
  point_list.push(height * (2 - freq / base_c));

  closest = freqs[targetNote].reduce((prev, curr) => {
    return Math.abs(curr - freq) < Math.abs(prev - freq) ? curr : prev;
  });
  shifter.pitch = Math.round(
    (freq < closest ? -1 : 1) *
      (12 * Math.log2(Math.min(freq, closest) / Math.max(freq, closest)))
  );
  drawAllPoints();
}
