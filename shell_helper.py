import subprocess
import sys
import os

cwd = r'c:\Users\studioo\Desktop\00000000000000000000_VICCA\nameo-elegant-furniture-shop-for-shopify-2023-11-27-05-20-50-utc\Nameo_v1.0.0\Theme-Packages\source\home1'
cmd = sys.argv[1:]

result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("EXIT CODE:", result.returncode)
