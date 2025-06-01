import re
import sys

filename = sys.argv[1]

with open(filename, 'r') as file:
    for line in file:
        if "[with " in line:
            match_filename = re.search(r'at line \d+ of (.+)', line)

            if match_filename:
                filename = match_filename.group(1)
                print(filename)
            
            match = re.search(r'\[with\s+(.+?)\]', line)
            if match:
                types = [t.strip() for t in match.group(1).split(',')]
                print('\n'.join(map(lambda x: f"\t{x}", types)))
        # if "warning" in line.lower():
        #     continue
        # if "error" in line.lower().replace("error-type", ""):
        #     print(line.strip())
        #     continue
        # if '/home/kjetil' in line:
        #     print(line.strip())