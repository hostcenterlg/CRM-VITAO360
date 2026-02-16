import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inspect_meta_acomp.py")
with open(OUT, "w", encoding="utf-8") as f:
    w = f.write
    # Build paths with unicode chars
    w("import openpyxl\n")
    w("from openpyxl.utils import get_column_letter\n")
    w("import os, sys\n\n")
    w("SEPARATOR = chr(61) * 100\n")
    w("SUB_SEP = chr(45) * 80\n\n")
print("Bootstrap phase 1 done:", os.path.getsize(OUT), "bytes")
