"""Run a RepDetector (detector.py by default) on every recording and score it.

python main.py                         summary over all recordings
python main.py --detail                plus one line per recording (expected, counted, error)
python main.py --exercise "PEC DECK"   only recordings whose exercise contains this text (case-insensitive)
python main.py --file 20261031_103907  only recordings whose file name contains this text
python main.py --data ../new_sets      score another folder of recordings (same CSV format)
python main.py --detector submissions/alice-bandpass/detector.py   score a submission

Score = MAE + 0.01 * RMSE of (counted - expected) over recordings. Lower is better. See AGENTS.md.
"""
import argparse
import importlib.util
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load_detector_class(path):
    """Import RepDetector from a detector file; its folder goes on sys.path so it can import its own modules."""
    path = Path(path).resolve()
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("submitted_detector", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RepDetector


def load(path):
    """Return (expected reps, exercise name, list of (sensor, t_seconds, x, y, z)) for one recording."""
    expected, exercise, rows = None, "", []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#reps,"):
                expected = int(line.split(",", 1)[1])
            elif line.startswith("#exercise,"):
                exercise = line.split(",", 1)[1].strip()
            elif line.startswith("#") or not line.strip():
                continue
            else:
                sensor, ts, x, y, z = line.split(",")
                rows.append((int(ts), sensor, float(x), float(y), float(z)))
    rows.sort(key=lambda r: r[0])
    t0 = rows[0][0]
    samples = [(sensor, (ts - t0) * 1e-9, x, y, z) for ts, sensor, x, y, z in rows]
    return expected, exercise, samples


def run(detector_class, samples):
    """Stream samples through a fresh detector; return the final count. Raises if the count ever decreases."""
    det = detector_class()
    last = 0
    for sensor, t, x, y, z in samples:
        det.add_sample(sensor, t, x, y, z)
        count = det.rep_count
        if count < last:
            raise RuntimeError(f"rep_count went down from {last} to {count} at t={t:.2f}s: counts must never be taken back")
        last = count
    return int(last)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--exercise", default="")
    ap.add_argument("--file", default="")
    ap.add_argument("--data", type=Path, default=DATA, help="folder of rep_*.csv recordings (default: data/)")
    ap.add_argument("--detector", type=Path, default=ROOT / "detector.py", help="file defining RepDetector (default: detector.py)")
    args = ap.parse_args()
    detector_class = load_detector_class(args.detector)

    errors, n_samples, elapsed = [], 0, 0.0
    detail = []
    for path in sorted(args.data.glob("rep_*.csv")):
        if args.file and args.file not in path.name:
            continue
        expected, exercise, samples = load(path)
        if args.exercise.lower() not in exercise.lower():
            continue
        start = time.perf_counter()
        counted = run(detector_class, samples)
        elapsed += time.perf_counter() - start
        n_samples += len(samples)
        errors.append(counted - expected)
        detail.append((path.stem[4:], exercise, expected, counted))

    if not errors:
        raise SystemExit("no recording matches the filters")

    if args.detail:
        print(f"{'file':16} {'exercise':46} {'exp':>4} {'got':>4} {'err':>4}")
        for name, exercise, expected, counted in detail:
            print(f"{name:16} {exercise[:46]:46} {expected:4d} {counted:4d} {counted - expected:+4d}")
        print()

    n = len(errors)
    mae = sum(abs(e) for e in errors) / n
    rmse = math.sqrt(sum(e * e for e in errors) / n)
    exact = sum(e == 0 for e in errors)
    bias = sum(errors) / n
    print(f"recordings={n}  exact={exact}/{n}  MAE={mae:.3f}  RMSE={rmse:.3f}  bias={bias:+.3f}")
    print(f"score = MAE + 0.01*RMSE = {mae + 0.01 * rmse:.4f}  (lower is better)")
    print(f"speed: {1e6 * elapsed / n_samples:.1f} us per sample")


if __name__ == "__main__":
    main()
