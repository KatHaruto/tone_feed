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
const point_num = 100;
const point_size = 3;
const freqs = new Array(12);
freqs[0] = [32.703, 65.406, 130.813, 261.626, 523.251, 1046.502];
for (let i = 1; i < freqs.length; i++) {
  freqs[i] = freqs[i - 1].map((v) => v * Math.pow(2, i / 12));
}
const targetNote = document.getElementById("target");
let base_c = 0;
let canvas;
let ctx;
let freq = 0;
let shifter = null;
let merger = null;
let isUpdate = true;
const d3 = 146.832;
function setup() {
  canvas = document.getElementById("myChart");
  canvas.width = width;
  canvas.height = height;
  ctx = canvas.getContext("2d");
  ctx.lineWidth = 10;
  ctx.strokeStyle = "#FF0000";
  ctx.lineCap = "round";
  mic = new p5.AudioIn();
  mic.start();
}

function touchStarted() {
  userStartAudio();
  getAudioContext().suspend();
  // このスケッチのAudioContextを返す
  // https://p5js.org/reference/#/p5.sound/getAudioContext
  if (getAudioContext().state !== "running") {
    // https://developer.mozilla.org/ja/docs/Web/API/AudioContext
    // AudioContextオブジェクト
    audioContext = getAudioContext();
    // あらかじめ中断させられた音声コンテキストの時間の進行を返す。
    audioContext.resume();
    Tone.context = audioContext;
    // ここから本格スタート
    startPitch();
    if (mic) {
      shifter = new Tone.PitchShift({
        pitch: 0,
      });

      merger = new Tone.Merge(2).connect(audioContext.destination, 0, 0);
      mic.connect(audioContext.destination, 1, 1);
      mic.connect(shifter);
      shifter.connect(merger);
    }
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
  isUpdate = true;
};
function drawnotes() {
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
  notes.map((note, i) => {
    ctx.fillText(note, 0, 10 + (height - 20) * (2 - Math.pow(2, i / 12)));
    ctx.beginPath();
    ctx.moveTo(10, 5 + (height - 20) * (2 - Math.pow(2, i / 12)));
    ctx.lineTo(width, 5 + (height - 20) * (2 - Math.pow(2, i / 12)));
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 5;
    ctx.stroke();
  });
}
function drawpoint(x, y) {
  ctx.beginPath();
  ctx.arc(x, y, point_size, (0 * Math.PI) / 180, (360 * Math.PI) / 180, false);
  ctx.fillStyle = "rgb(255,0,0)";
  ctx.fill();
  ctx.restore();
}
function draw() {
  ctx.clearRect(0, 0, width, height);
  drawnotes();
  if (point_list.length > point_num) {
    point_list.shift();
  }
  if (freq > 0) {
    base_c = freqs[0].filter((e) => e <= freq).slice(-1)[0];
    freq_co = height * (2 - freq / base_c);
    point_list.push(freq_co);

    if (isUpdate) {
      isUpdate = false;
    }
    target = freqs[targetNote.value].filter((e) => e >= base_c)[0];
    distance_from_base_c = Math.round(12 * Math.log2(freq / base_c));
    distance_from_target_base_c = Math.round(12 * Math.log2(target / base_c));

    shifter.pitch =
      freq < target * Math.pow(2, 1 / 2)
        ? distance_from_target_base_c - distance_from_base_c
        : 12 - distance_from_target_base_c - distance_from_base_c;

    console.log(shifter.pitch, target);
  }
  //console.log(point_list);
  point_list.map((p, i) => {
    drawpoint(
      width / 2 - (width / 2 / point_num) * (point_list.length - i),
      7.5 + p
    );
  });
  ctx.beginPath();
  ctx.arc(
    width / 2,
    7.5 + height * (2 - target / base_c),
    point_size,
    (0 * Math.PI) / 180,
    (360 * Math.PI) / 180,
    false
  );
  ctx.fillStyle = "rgb(0,255,0)";
  ctx.fill();
  ctx.restore();
}
