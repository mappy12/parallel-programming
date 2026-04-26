import os
import sys
import re
import subprocess
import csv
import shutil

SIZES = [200, 400, 800, 1200, 1600, 2000]
BLOCK_SIZES = [8, 16, 32]
STATS_FILE = 'stats_cuda.csv'
EXE_NAME = 'matrix_cuda.exe'
SRC_DIR = 'src'
EXE_PATH = os.path.join(SRC_DIR, EXE_NAME)

def find_vcvarsall():
    paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
    ]

    for path in paths:
        if os.path.exists(path):
            return path
    return None

VCVARSALL_PATH = find_vcvarsall()

def run_in_vs_env(command, description):
    print(f"{description}...")

    if not VCVARSALL_PATH:
        print("    Предупреждение: vcvarsall.bat не найден. Попытка запуска напрямую...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
    else:
        full_command = f'cmd /c "{VCVARSALL_PATH}" x64 && {command}'
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        err_msg = result.stderr.strip() or result.stdout.strip()
        if len(err_msg) > 200:
            err_msg = err_msg[:200] + "..."
        if err_msg:
            print(f"    Ошибка: {err_msg}")
        return False, ""
    return True, result.stdout

def main():
    print("Запуск серии экспериментов CUDA...")
    print("=" * 50)

    if VCVARSALL_PATH:
        print(f"Среда разработчика найдена: {VCVARSALL_PATH}")
    else:
        print("Среда разработчика не найдена автоматически. Убедитесь, что вы запустили этот скрипт из Developer Command Prompt.")

    if not os.path.exists(os.path.join(SRC_DIR, 'main.cu')):
        print(f"Файл {SRC_DIR}/main.cu не найден!")
        return

    results = []

    for n in SIZES:
        for block in BLOCK_SIZES:
            print(f"\nТест: N = {n}, Блок = {block}x{block}")

            success, _ = run_in_vs_env(f"python generate.py {n}", "Генерация матриц")
            if not success:
                success, _ = run_in_vs_env(f"python3 generate.py {n}", "Генерация матриц (альтернатива)")

            if not success:
                continue

            if not os.path.exists(EXE_PATH):
                compile_cmd = f'nvcc -allow-unsupported-compiler -O2 -std=c++11 -o {EXE_PATH} {SRC_DIR}/main.cu'
                success, output = run_in_vs_env(compile_cmd, "Компиляция CUDA проекта")
                if not success:
                    print("Критическая ошибка компиляции. Прерывание.")
                    return
                print("Компиляция успешна.")

            run_cmd = f"{EXE_PATH} {block}"
            success, output = run_in_vs_env(run_cmd, f"Запуск CUDA (блок {block})")

            if not success:
                continue

            time_match = re.search(r"(?:Computation time|Total time \(Copy \+ Compute\)):\s*([\d.]+)\s*seconds", output)
            exec_time = 0.0

            if time_match:
                exec_time = float(time_match.group(1))
                print(f"    Время: {exec_time} сек")
            else:
                print("    Не удалось найти время в выводе")
                continue

            operations = n ** 3

            success_verify, output_verify = run_in_vs_env("python verify.py", "Проверка результата")
            if not success_verify:
                success_verify, output_verify = run_in_vs_env("python3 verify.py", "Проверка результата (альтернатива)")

            is_correct = "PASSED" if (success_verify and "PASSED" in output_verify) else "FAILED"
            print(f"    Статус: {is_correct}")

            results.append({
                'Size': n,
                'BlockSize': block,
                'Time_sec': exec_time,
                'Operations': operations,
                'Status': is_correct
            })

    base_times = {}
    for r in results:
        if r['BlockSize'] == 8 and r['Time_sec'] > 0:
            base_times[r['Size']] = r['Time_sec']

    for r in results:
        n = r['Size']
        t_p = r['Time_sec']
        p = r['BlockSize']

        if n in base_times and t_p > 0:
            t_base = base_times[n]
            r['Speedup'] = round(t_base / t_p, 2)
            ideal_ratio = (p * p) / 64.0
            if ideal_ratio > 0:
                r['Efficiency'] = round((r['Speedup'] / ideal_ratio) * 100, 1)
            else:
                r['Efficiency'] = 0.0
        else:
            r['Speedup'] = 1.0
            r['Efficiency'] = 100.0

    if results:
        with open(STATS_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Size', 'BlockSize', 'Time_sec', 'Speedup', 'Efficiency', 'Operations', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nРезультаты сохранены в {STATS_FILE}")
    else:
        print("\nРезультаты не получены.")

if __name__ == "__main__":
    main()