import numpy as np
import sys

def load_matrix(filename):
    """Читает матрицу из файла формата: первая строка - размер, далее данные."""

    file = open(filename, 'r')

    # Первая строка - это размер матрицы
    n = int(file.readline())

    matrix = []

    for line in file:
        if line.strip():
            row = [float(x) for x in line.split()]
            matrix.append(row)

    file.close()

    return matrix

def main():

    print("ПРОВЕРКА НАЧАТА...")

    try:
        A = load_matrix('data/matrixA.txt')
        B = load_matrix('data/matrixB.txt')
        C_cpp = load_matrix('data/matrixC.txt')

        A_np = np.array(A)
        B_np = np.array(B)
        C_np = np.array(C_cpp)

        C_correct = np.dot(A_np, B_np)

        print("Результат:")
        if np.allclose(C_np, C_correct):
            print("    Пройдена(PASSED)")

        else:
            print("FAILED")
            diff = np.abs(C_np - C_correct)
            print(f"Максимальная ошибка: {np.max(diff)}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
