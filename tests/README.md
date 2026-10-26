# Unit tests

Run `.venv/bin/python -m unittest discover -s tests -v` from the project root. Fifteen tests use explicitly synthetic fixtures to check pair identity, frame alignment, bumper geometry, nonclosing conditions, units, common support, short trajectories, events, overlap matching, lane/time breaks and exact zero velocity on stationary positions. Synthetic fixtures are not research observations. Real-run verification is performed by scripts/verify.py.
