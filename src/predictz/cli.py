import argparse

from predictz.predict import predict_upcoming
from predictz.sync import sync_football, sync_history
from predictz.tracking import log_predictions, score_predictions, show_scored


def main():
    parser = argparse.ArgumentParser(prog="predictz")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync", help="refresh data, then log predictions for new fixtures")
    sub.add_parser("score", help="score logged predictions against real results")
    r = sub.add_parser("review", help="show each scored prediction next to its result")
    r.add_argument("--model", default="elo-v2")
    r.add_argument("--competition", default=None, help="PL, PD or SA")
    p = sub.add_parser("predict", help="show predictions for upcoming fixtures")
    p.add_argument("--competition", default="PL")
    p.add_argument("--n", type=int, default=10, help="how many fixtures to show")
    args = parser.parse_args()

    if args.cmd == "sync":
        sync_history()
        sync_football()
        log_predictions()
    elif args.cmd == "score":
        score_predictions()
    elif args.cmd == "review":
        show_scored(args.model, args.competition)
    else:
        predict_upcoming(args.competition, args.n)


if __name__ == "__main__":
    main()