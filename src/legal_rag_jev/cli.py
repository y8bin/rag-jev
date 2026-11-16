"""Command line for the current KoBLEX ParSeR study."""
from pathlib import Path
import runpy

def main():
    entry=Path(__file__).resolve().parents[2]/"scripts/koblex.py"
    runpy.run_path(str(entry),run_name="__main__")

if __name__=="__main__":main()
