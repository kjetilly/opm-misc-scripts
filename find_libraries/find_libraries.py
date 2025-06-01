import datetime
import subprocess
import sys
import os
import re
import copy

error_file = sys.argv[1]
# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(script_dir, 'build_hip')
source_file = os.path.join(script_dir, 'opm-simulators', 'tests', 'gpuistl', 'test_gpuflowproblemall.cu')

includes_source = []
def find_symbols_in_object(filepath):
    symbols = []
    cmd = ['llvm-nm', '-C', '--defined-only', filepath]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                symbols.append(' '.join(parts[2:]).strip().replace(' ', ''))
        return symbols
    except subprocess.CalledProcessError as e:
        raise e
def find_include_objects(symbol, classname, returntype, directory=build_dir):
    if 'extendEval' in symbol:
        print("here")
    for opm_dir in ['opm-common', 'opm-grid', 'opm-simulators']:
        opm_dir = os.path.join(opm_dir, 'CMakeFiles', f"{opm_dir.replace('-','')}.dir")
        for root, dir, files in os.walk(os.path.join(directory, opm_dir, 'opm')):
            for file in files:
                if file.endswith('.cpp.o'):
                
                    file_path = os.path.join(root, file)
                    symbols = find_symbols_in_object(file_path)
                    for symbol_potential in symbols:
                        if 'extendEval' in symbol_potential and 'extendEval' in symbol:
                            print(f"{symbol_potential} in {file_path}")
                            print(f"{symbol}")
                            print(f"Matches: {symbol_potential == symbol}")
                    if symbol.strip().replace(' ', '') in symbols:
                        cppfilename = file_path.replace('.cpp.o', '.cpp')
                        return os.path.relpath(cppfilename, os.path.join(directory, opm_dir))
    
def find_include(symbol, classname, returntype, directory=script_dir):
    """
    Find the include file for a given symbol and classname.
    """
    for opm_dir in ['opm-common', 'opm-grid', 'opm-simulators']:
        for root, dir, files in os.walk(os.path.join(directory, opm_dir, 'opm')):
            for file in files:
                if file.endswith('.cpp') or file.endswith('.cu') or file.endswith('_impl.hpp'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:

                            previous_line = ""
                            for content in f:

                                content=content.strip()
                                if previous_line.strip().endswith("::"):
                                    content = previous_line + content.strip()
                                if content.strip().startswith('#include'):
                                    continue
                                if content.strip().startswith('//'):
                                    continue
                                if content.strip().endswith(';'):
                                    continue
                                if '->' in content:
                                    continue
                                if classname is not None:
                                    if symbol in content and classname in content and returntype in content and "::" in content:
                                        match = re.search(rf'{classname}\s*\s*(<((?!->)[^>])+>)?\s*::\s*{symbol}', content)
                                        if match:
                                            index_first_paranthesis = min(content.find('['), content.find('('))
                                            if index_first_paranthesis != -1:
                                                index_match = match.start()
                                                if index_match > index_first_paranthesis:
                                                    continue
                                            #print(f"Found {symbol} in {file_path} with clas '{classname}'")
                                            #print(f"\t{content.strip()}")
                                            return os.path.relpath(file_path, os.path.join(directory, opm_dir))
                                else:

                                    if symbol in content and returntype in content:
                                        if returntype == '' or returntype is None:
                                            match = re.search(rf'{symbol}', content)
                                        else:
                                            match = re.search(rf'{returntype}\s+{symbol}', content)
                                        
                                        if match:
                                            
                                            #print(f"Found function {symbol} in {file_path}")
                                            #print(f"\t{content.strip()}")
                                            return os.path.relpath(file_path, os.path.join(directory, opm_dir))
                                previous_line = content
                                       
                    except UnicodeDecodeError:
                        #print(f"Skipping file {file_path} due to encoding error.")
                        continue
    return None#print(f"Warning: Could not find include for symbol '{symbol}' with classname '{classname}' and returntype '{returntype}'.")

with open(source_file, 'r') as f:
    for line in f:
        if line.startswith('#include'):
            parts = line.split('"')
            if len(parts) > 1:
                include_path = parts[1].strip()
                includes_source.append(include_path)
            else:
                parts = line.split('<')
                if len(parts) > 1:
                    include_path = parts[1].replace('>', '').strip()
                    includes_source.append(include_path)
includes_source_orig = copy.deepcopy(includes_source)
files_to_include = []
with open (error_file, 'r') as f:
    for line in f:
        if 'undefined symbol' in line:
            parts = line.split('undefined symbol: ')
            if len(parts) > 1:
                symbol = parts[1].strip()
                origsymbol = symbol

                #print(symbol)
                match = re.search(r'(([a-zA-Z0-9_]+)\s+)?([a-zA-Z0-9_]+(<[^>]+\>)?::)*([a-zA-Z0-9_]+)(<[^>]+\>)?::([a-zA-Z0-9_]+)\s*(<[^>]+\>)?\s*?\s*\(', symbol)
                if match:
                    #print(symbol, end=' ')
                    symbol = match.group(len(match.groups())-1).strip()
                    classname = match.group(len(match.groups())-3) if match.group(len(match.groups())-3) else None
                    returntype = match.group(1) if match.group(1) else ""
                    if classname in ['std', 'Opm', 'gpuistl', 'detail', 'Dune']:
                        classname = None
                    include_file = find_include(symbol, classname, returntype)
                    
                    if include_file is None:

                        include_file = find_include_objects(origsymbol, classname, returntype)
                    if include_file is None:
                        #print(f"Warning: Could not find include for symbol '{symbol}' with classname '{classname}' and returntype '{returntype}'.\n\t{origsymbol}")
                        continue
                    if include_file in includes_source_orig or include_file in includes_source:
                        include_file = find_include_objects(origsymbol, classname, returntype)
                    if include_file is None:
                        continue
                    if include_file in files_to_include:
                        continue
                        #print(f"Warning: Include file '{include_file}' already exists in the source file. Skipping.")
                        #print(f"Was to be added for symbol '{symbol}' with classname '{classname}' and returntype '{returntype}'.\n\t{origsymbol}")
                    if include_file in includes_source:
                        continue
                    if include_file is not None:
                        files_to_include.append(include_file)
                        includes_source.append(include_file)
                else:
                    include_file = find_include_objects(origsymbol, None, None)
                    if include_file is None:
                        #print(f"Warning: Could not find include for symbol '{symbol}' with classname '{classname}' and returntype '{returntype}'.\n\t{origsymbol}")
                        continue
                    if include_file in includes_source_orig or include_file in includes_source:
                        continue
                    includes_source.append(include_file)
                    files_to_include.append(include_file)

                       
if len(files_to_include) != 0:
    with open(source_file, 'a') as f:
        f.write("//"* 80 + "\n")
        f.write("// Automatically added includes for undefined symbols\n")
        f.write(f"// Added at datetime: {datetime.datetime.now()}\n")
        f.write("//"* 80 + "\n")
        for include in files_to_include:
            f.write("#include <" + include + ">\n")