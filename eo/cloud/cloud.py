import argparse
import subprocess

cpp_executable = "./cloud"

parser = argparse.ArgumentParser(
    prog='TIF Cloud Remover',
    description='Removes cloud pixels from a TIF'
)
parser.add_argument('tif')
args = parser.parse_args()
tif = args.tif

result = subprocess.run([cpp_executable, tif], capture_output=True, text=True)
print(result.stdout.strip())
print(result.stderr.strip())