import csv
import subprocess
import sys

def calculate_cfr(history):
    # CFR is the percentage of failures (represented by '1' in the history)
    # E.g., '10101' -> 3 failures out of 5 runs -> 0.6 CFR
    if not history:
        return 0.0
    failures = history.count('1')
    return failures / len(history)

def optimize_and_run():
    test_mapping = {
        'TC_03_01': 'tests/test_unit.py::test_valid_trainer_registration_tc01',
        'TC_03_02': 'tests/test_unit.py::test_empty_username_tc02',
        'TC_03_03': 'tests/test_unit.py::test_mismatch_password_tc03'
    }

    test_cases = []
    
    # Read the test data CSV
    try:
        with open('test_data.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                test_id = row['test_id']
                feature = row['feature']
                execution_time = float(row['time'])
                history = row['history']
                risk = int(row['risk'])
                
                cfr = calculate_cfr(history)
                # Formula: Score = (CFR * Risk) / Execution Time
                score = (cfr * risk) / execution_time
                
                test_cases.append({
                    'test_id': test_id,
                    'feature': feature,
                    'time': execution_time,
                    'cfr': cfr,
                    'risk': risk,
                    'score': score,
                    'pytest_path': test_mapping.get(test_id)
                })
    except FileNotFoundError:
        print("Error: test_data.csv not found.")
        sys.exit(1)

    # Sort test cases by optimization score in descending order
    test_cases.sort(key=lambda x: x['score'], reverse=True)

    print("\n==================================================")
    print("           TEST PRIORITIZATION RESULTS            ")
    print("==================================================")
    print(f"{'Priority':<10}{'Test ID':<10}{'Feature':<20}{'Score':<10}")
    print("--------------------------------------------------")
    for idx, tc in enumerate(test_cases, 1):
        print(f"{idx:<10}{tc['test_id']:<10}{tc['feature']:<20}{tc['score']:.4f}")
    print("==================================================\n")

    # Build the pytest command with tests in sorted order
    cmd = [sys.executable, '-m', 'pytest', '-v', '--junitxml=results.xml']
    for tc in test_cases:
        if tc['pytest_path']:
            cmd.append(tc['pytest_path'])
            
    print(f"Running optimized test suite in prioritized order:\n{' '.join(cmd)}\n")
    
    # Run the tests
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    optimize_and_run()
