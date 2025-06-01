import subprocess
import os
import time

def compile():
    try:
        with open('allerrors.txt', 'w') as f:
            result = subprocess.run(['ninja', '-j15', 'test_gpuflowproblemall'], capture_output=True, text=True)
            f.write(result.stdout)
            f.write(result.stderr)
        return result.returncode == 0
    except Exception:
        return False
def get_number_of_lines(filename):
    with open(filename, 'r') as f:
        return sum(1 for _ in f)
    
def find_libraries(script, output_file):
    try:
        result = subprocess.run(['python3', script, output_file], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running script {script}: {e}")
        return False
def run_to_failure(script, source_file):
    while True:
        number_of_lines_before = get_number_of_lines(source_file)
        start = time.time()
        compile_result = compile()
        end = time.time()
        print(f"Compilation took {end - start:.2f} seconds.")
        with open("compilation_times.txt", "a") as f:
            f.write(f"{number_of_lines_before},{end - start:.2f}\n")
        if compile_result:
            return
        else:
            find_libraries(script, "allerrors.txt")
            number_of_lines_after = get_number_of_lines(source_file)
            if number_of_lines_before == number_of_lines_after:
                print("No new lines added to the source file. Stopping.")
                return
            else:
                print(f"New lines added to {source_file}. Continuing...")

   
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(script_dir, 'opm-simulators', 'tests', 'gpuistl', 'test_gpuflowproblemall.cu')
    script = os.path.join(script_dir, 'find_libraries.py')
    run_to_failure(script, source_file)