import os.path
import re
import subprocess
import csv

SIZES = [200, 400, 800, 1200, 1600, 2000]

STATS_FILE = 'stats_omp.csv'

THREADS = [1, 2, 4, 8]

EXE_PATH = 'src/matrix'

def run_command(command, description):
    """Выполняет команду и возвращает (успех, вывод)."""
    
    print(f"{description}...")

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    Ошибка: {result.stderr.strip()}")
        return False, ""
    return True, result.stdout

def main():
    print("Запуск серии экспериментов...")
    print("=" * 50)

    if not os.path.exists(EXE_PATH):
        print(f"Файл {EXE_PATH} не найден!")
        print("Чтобы скомпилировать код:"
              "    g++ -fopenmp -O2 -std=c++11 -o src/matrix src/main.cpp")
        return

    results = []

    for n in SIZES:
        for threads in THREADS:

            print(f"\nТест для размера N = {n}, Потоки = {threads}")

            success, _ = run_command(f"python3 generate.py {n}",
                                     "Генерация матриц")

            if not success:
                continue

            env = os.environ.copy()
            env['OMP_NUM_THREADS'] = str(threads)

            success, output = run_command(EXE_PATH, f"Запуск программы умножения ({threads} потоков)")

            if not success:
                continue

            time_match = re.search(r"Computation time:\s*([\d.]+)\s*seconds",
                                   output)

            exec_time = 0.0
            if time_match:
                exec_time = float(time_match.group(1))
                print(f"    Время выполнения: {exec_time} сек")

            else:
                print("    Не удалось найти время в выводе программы")

            operations = n ** 3
            print(f"    Объем задачи (N^3): {operations:,} операций")

            success_verify, output_verify = run_command("python3 verify.py",
                                            "Проверка результата (verify.py)")

            if success_verify and "PASSED" in output_verify:
                is_correct = "PASSED"
            else:
                is_correct = "FAILED"

            if is_correct == "PASSED":
                print("Проверка ПРОЙДЕНА")
            else:
                print("Проверка НЕ ПРОЙДЕНА")

            results.append({
                'Size': n,
                'Time_sec': exec_time,
                'Operations': operations,
                'Status': is_correct
            })

    if results:
        with open(STATS_FILE, 'w', newline='', encoding='utf-8') as f:

            fieldnames = ['Size', 'Time_sec', 'Operations', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(results)

        print("\n" + "=" * 50)
        print(f"Результаты сохранены в файл: {STATS_FILE}")
        print("=" * 50)

if __name__ == "__main__":
    main()
