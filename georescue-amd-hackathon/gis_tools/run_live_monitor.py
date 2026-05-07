"""Run repeated near-real-time flood analysis cycles."""

import argparse
import logging
import time

from run_live_cycle import run_cycle


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_monitor(interval_seconds: int) -> None:
    cycle = 0
    logger.info("Starting live monitor with %s second interval", interval_seconds)

    while True:
        cycle += 1
        logger.info("Starting cycle #%s", cycle)
        try:
            run_cycle()
            logger.info("Cycle #%s finished", cycle)
        except Exception as exc:
            logger.error("Cycle #%s failed: %s", cycle, exc)

        time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run live flood monitor")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=300,
        help="How often to refresh live data and flood analysis",
    )
    args = parser.parse_args()

    run_monitor(interval_seconds=args.interval_seconds)