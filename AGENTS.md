# Implementing the rep detector

This file is self-contained: it is everything you need to implement `RepDetector` in `detector.py`.

**Goal: the best possible rep counter.** Any idea is welcome — signal processing, state machines, learned models,
rhythm or tempo cues, sensor fusion. The only limits are the four product constraints
below; everything else is judged by the score on recordings collected after yours.

## The problem

A workout app counts repetitions **live**, while the user does a set on a gym machine, using the phone's motion
sensors. The phone is laid on the machine, usually on top of a cable machine's weight stack (or on the part of the
machine that moves), so every rep moves the phone up and down (or back and forth) once. The app shows the count as
it goes; it is never corrected after the fact.

Your job: given the sensor samples of one set, streamed one at a time, count the reps.

## Repository

```
detector.py     RepDetector, the class to implement (empty stub: always counts 0)
main.py         streams every recording through a RepDetector and prints the score
data/           one CSV per set (168 recordings)
submissions/    one folder per submitted detector (see "Submitting")
LEADERBOARD.md  scores of the submissions
```

Run it:

```
python main.py                         # summary
python main.py --detail                # per-recording expected / counted / error
python main.py --exercise "hip"        # filter by exercise name
python main.py --file 20261031_103907  # filter by file name
python main.py --data some/folder      # score another folder of recordings
python main.py --detector submissions/alice-bandpass/detector.py   # score a submission
```

Python 3.8+. `main.py` uses only the standard library. The detector may use any Python package, as long as the
method can be ported to an Android phone (constraint 3).

## Interface

```python
class RepDetector:
    def __init__(self): ...                                  # fresh detector, start of a set
    def add_sample(self, sensor, t, x, y, z) -> None: ...    # one sensor sample
    @property
    def rep_count(self) -> int: ...                          # reps counted so far
```

- `main.py` creates a new `RepDetector()` for each recording (one instance = one set, never reused), calls
  `add_sample` for every sample of every sensor in time order, and reads `rep_count` after **each** sample. The
  value after the last sample is the answer.
- `sensor`: one of
  - `"accelerometer"`: raw acceleration, gravity included (a phone lying still reads a magnitude of about 9.81);
  - `"gravity"`: Android's fused estimate of the gravity vector (`TYPE_GRAVITY`);
  - `"linear"`: Android's fused acceleration minus gravity (`TYPE_LINEAR_ACCELERATION`); can start at 0,0,0
    while the fusion warms up.
- `t`: seconds since the first sample of the set, non-decreasing across sensors. Each sensor runs at roughly
  200 Hz with irregular spacing; the three streams are interleaved. Resample internally if you want a fixed rate.
- `x, y, z`: m/s², in the phone's coordinate frame.
- `rep_count` must **never decrease**. `main.py` stops with an error if it does.

## Data

`data/rep_YYYYMMDD_HHMMSS.csv`, one file per set, named by recording time:

```
#reps,8                         label: number of reps actually done (ground truth)
#exercise,PEC DECK              exercise name (for analysis only: the detector does not get it)
#comment,"..."                  optional note from the user, in French (e.g. "6 or 7" = unsure label)
#columns,sensor,timestamp_ns,x,y,z
accelerometer,776574443404982,-0.07597212,9.88475,1.0339985
gravity,776574447104097,-0.07488878,9.753157,1.0201609
linear,776574447104097,0.0,0.0,0.0
...
```

- Only the total count is labelled; there are no per-rep timestamps.
- A recording starts when the user presses start and ends when they press stop, so there is some idle time and
  phone handling at both ends.
- Labels are counted by the user and may occasionally be off by one.
- Rows are not strictly sorted by timestamp across sensors; `main.py` sorts them.
- Exercises (count): Triceps Extension 29, Technogym Leg Press 28, Cable Crossovers 23, Leg Extension 18, Seated
  Leg Curl 13, Horizontal Row 12, PEC DECK 10, Lying Leg Curls 7, Hip Abductor 6, Leg Press / Machine Leg Press 6,
  Hip Adductor 4, Facepulls 3, Pull-ups 3, and a few others. Sets are mostly 5–15 reps, 20–60 s long, roughly 1.5–5 s per rep.
- Known hard cases: small-motion machines (Hip Abductor / Adductor, PEC DECK), where the stack barely moves; a slow
  or partial last rep; pauses mid-set; reps slowing down as the user tires; two reps that blur into one.
- Pull-ups are the exception to the phone-on-the-machine setup: the phone is carried on the body.

## Constraints

These come from the product, not from what worked before. A detector that breaks one cannot ship, whatever its
score.

1. **Live and causal.** The detector sees samples one at a time and may only use the past. A rep, once counted,
   is never taken back (`rep_count` never decreases). Counting a rep a little after it ends is fine; waiting for
   the end of the set to decide is not.
2. **No extra user effort or context.** No calibration set, no correction button, no question to the user. The
   detector gets only the sensor stream of the current set: no exercise name, no previous sets.
3. **Runs on a phone in real time.** It will be ported to Java on Android: bounded memory and bounded work per
   sample, no server. A learned model is fine if it is small enough to run on a phone at this sample rate, and you
   ship its weights. `main.py` prints the time per sample.
4. **One method for all recordings.** No per-file settings, no code that recognises specific recordings or
   hard-codes their counts. It must also work on machines and exercises that are not in this data.

Everything else is allowed. For what it's worth, the current app detector uses only the accelerometer magnitude
and no rhythm logic, and a tiny neural net tried on this data memorised it — treat that as a data point, not a rule.

## Scoring

For each recording, `error = counted − expected`. Over all recordings:

- **score = MAE + 0.01 × RMSE** (lower is better). MAE drives it; RMSE breaks ties in favour of fewer big misses.
- Also reported: `exact` (recordings counted exactly), `bias` (mean error: negative = undercount).

**The score that counts is on recordings made after this repository was published** (same users, gym and
format, later dates), scored with `python main.py --data <folder of new recordings>`. With only 168 sets, a method
can fit these labels without generalising; the future recordings are what tells.

Reference, the detector currently in the app (a hand-tuned DSP method, not published here), on `data/`: **exact
125/168, MAE 0.357, RMSE 0.809, score 0.3652**. Partly in-sample: it was tuned on the 111 non-pull-up recordings up
to 2026-11-09. On the 25 recordings from 2026-11-16 on, which it never saw, it gets 13/25, MAE 0.720. The empty
stub scores about MAE 9.

## Tips

- Plot the accelerometer magnitude for a few files first (`--detail` shows which ones are hard). Reps show as a slow
  oscillation (well under 1 Hz) riding on 9.81, with noise and spikes from handling at the start and end.
- Amplitude varies a lot between machines (leg press vs hip abductor), so fixed absolute thresholds tend to fail
  on one end or the other.
- Simulate the future recordings yourself: tune on older recordings (file names are dates), score the newest ones, and
  only trust gains that hold there.
- Keep the final `detector.py` self-contained, with its parameters (or model weights) included and a short
  description of the method at the top.

## Submitting

Submissions are pull requests to this repository. Work on a copy of `detector.py`, then:

1. **Create `submissions/<your-name>-<method>/`** (lowercase, dashes, e.g. `alice-bandpass-fsm`). Do not edit
   `main.py`, `data/`, the root `detector.py` or other submissions.
2. **Put your detector in `detector.py` in that folder**, defining `RepDetector` with the interface above. It may
   import other files from its own folder (they are importable when it is loaded). Include everything needed to
   run it: parameters, model weights (keep them small), helper modules. No downloads or network at run time.
3. **Check it runs from the repository root** and copy the output:
   ```
   python main.py --detector submissions/<your-name>-<method>/detector.py
   ```
   It must finish without error on every recording and give the same result on every run (fix random seeds).
4. **Add `NOTES.md` in the folder** with:
   - **Method:** how it works, in enough detail to port it to Java (signals used, filters, decision logic).
   - **Score:** the summary lines printed by `main.py` (exact, MAE, RMSE, bias, score, speed).
   - **Tuning:** what was fitted and on which recordings (e.g. "thresholds grid-searched on files before
     20261110, checked on the rest"), and the score on the recordings you did not tune on.
   - **Dependencies:** Python packages beyond the standard library (plus a `requirements.txt` if any).
   - **Phone cost:** rough memory and work per sample, model size if any.
   - **Constraints:** one line per constraint (1–4) saying how the detector respects it.
5. **Optional:** training or tuning scripts in the folder, so the result can be reproduced.
6. **Open a pull request** titled `Submission: <your-name>-<method> (score X.XXXX)`, with the NOTES.md summary as
   its description.

Maintainers check the constraints, score the detector on recordings collected after the pull request, and add a
row to `LEADERBOARD.md`. A submission that breaks a constraint is not ranked, whatever its score. To improve a
submission, add a new folder (`alice-bandpass-fsm-v2`) rather than editing a ranked one.
