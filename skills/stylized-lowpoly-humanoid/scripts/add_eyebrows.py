"""Kept for old commands (ledger #326 gate): forwards to eyebrow_fitter.py — landmark fit + raycast + surface-normal offset."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eyebrow_fitter import cli

if __name__ == "__main__":
    cli()
