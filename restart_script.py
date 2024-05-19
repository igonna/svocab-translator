from subprocess import run
from time import sleep

# Path and name to the script you are trying to start
file_path = "openai_client.py"

# Example arguments to be passed to the script
args = ["/Users/c/Documents/svocab_data/datasets/words_output/de.txt"]

restart_timer = 55

def start_script():
    try:
        # Construct the command as a list with the python interpreter, script, and arguments
        command = ["python3", file_path] + args
        # Run the command
        run(command, check=True)
    except:
        # Script crashed, let's restart it!
        handle_crash()

def handle_crash():
    sleep(restart_timer)  # Restarts the script after 2 seconds
    start_script()

start_script()