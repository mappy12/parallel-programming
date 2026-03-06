import random
import sys
import os

def gen_matrix(n, filename):
    """Генерация матрицы"""

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        f.write(f"{n}\n")
        for i in range(n):
            row = [round(random.uniform(1.0, 10.0), 4) for _ in range(n)]
            f.write(" ".join(map(str, row)) + "\n")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    print(f"Generating {n}x{n} matrices...")
    gen_matrix(n, "data/matrixA.txt")
    gen_matrix(n, "data/matrixB.txt")
    print("Done!")
