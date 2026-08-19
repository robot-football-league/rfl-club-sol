"""Play a practice match: this club versus a mirror copy of itself.

    ../rfl-engine/.venv/bin/python tools/practice.py --time 90

This utility lives under tools/ because club scrutineering checks every
top-level Python file as match code. Analysis and practice tools are exempt.
"""

import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", type=float, default=60.0)
    ap.add_argument("--video", default=None)
    ap.add_argument("--opponent", default=None,
                    help="path to another team dir (default: mirror match)")
    ap.add_argument("--out", default="runs/practice")
    args = ap.parse_args()

    club = Path(__file__).resolve().parent.parent
    other = Path(args.opponent).resolve() if args.opponent else club
    from gauntlet.rfl import run_rfl_match
    res = run_rfl_match(str(club), str(other), match_time_s=args.time,
                        video_path=args.video, log_dir=args.out)
    print(f"final score: {res.score[0]} - {res.score[1]}")
    print(f"logs: {args.out}/")


if __name__ == "__main__":
    main()
