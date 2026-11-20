#!/usr/bin/env python3
"""News-image entry (Python 3.13, standard library only): the entry image is
entry.png beside this file, and the program copies it to /output/entry.png.
The gate takes a whole PNG or JPEG of at most 1 MiB and 1024 by 1024 pixels,
and the judge sees exactly the bytes copied.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import shutil
from pathlib import Path

src = Path(__file__).resolve().parent / "entry.png"
out = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
out.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src, out)
