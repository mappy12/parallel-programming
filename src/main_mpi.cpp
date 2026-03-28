#include <iostream>
#include <vector>
#include <chrono>
#include <fstream>
#include <stdexcept>
#include <mpi.h>

using namespace std;

vector<vector<double>> multMatrix(
    const vector<vector<double>> &A,
    const vector<vector<double>> &B,
    int n) {

    vector<vector<double>> C(n, vector<double>(n, 0.0));

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            for (int k = 0; k < n; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }

    return C;
}

vector<vector<double>> readMatrix(const string& filename, int& n) {
    ifstream file(filename);

    if (!file.is_open()) {
        cerr << "ERROR: Could not open file " << filename << endl;
        exit(1);  
    }

    file >> n;

    vector<vector<double>> matrix(n, vector<double>(n, 0.0));

    for (int i=0; i < n; i++)
        for (int j=0; j < n; j++)
            file >> matrix[i][j];

    return matrix;
}

void writeMatrix(
    const string& filename,
    const vector<vector<double>>& matrix,
    int n) {

    ofstream file(filename);

    if (!file.is_open()) {
        cerr << "ERROR: Could not write file " << filename << endl;
        exit(1);
    }

    file << n << endl;

    for (int i=0; i < n; i++) {
        for (int j=0; j < n; j++)
            file << matrix[i][j] << " ";

        file << endl;
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int n;
    vector<vector<double>> A, B, C;

    if (rank == 0) {
        int n1, n2;

        A = readMatrix("data/matrixA.txt", n1);
        B = readMatrix("data/matrixB.txt", n2);

        if (n1 != n2) {
            cout << "Matrices must be same size" << endl;
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        n = n1;
    }

    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int rows = n / size;
    int remainder = n % size;

    int local_rows = rows + (rank < remainder ? 1 : 0);

    vector<vector<double>> localA(local_rows, vector<double>(n));
    vector<vector<double>> localC(local_rows, vector<double>(n, 0.0));

    vector<double> flatB(n * n);

    if (rank == 0) {
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                flatB[i * n + j] = B[i][j];
    }

    MPI_Bcast(flatB.data(), n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        int offset = 0;

        for (int p = 0; p < size; ++p) {
            int send_rows = rows + (p < remainder ? 1 : 0);

            if (p == 0) {
                for (int i = 0; i < send_rows; ++i)
                    localA[i] = A[i];
            } else {
                MPI_Send(&A[offset][0],
                    send_rows * n,
                    MPI_DOUBLE,
                    p,
                    0,
                    MPI_COMM_WORLD);
            }

            offset += send_rows;
        }
    } else {
        MPI_Recv(&localA[0][0],
            local_rows * n,
            MPI_DOUBLE,
            0,
            0,
            MPI_COMM_WORLD,
            MPI_STATUS_IGNORE
            );
    }

    MPI_Barrier(MPI_COMM_WORLD);

    auto start = chrono::high_resolution_clock::now();

    for (int i = 0; i < local_rows; ++i) {
        for (int j = 0; j < n; ++j) {
            for (int k = 0; k < n; ++k) {
                localC[i][j] += localA[i][k] * flatB[k * n + j];
            }
        }
    }

    auto end = chrono::high_resolution_clock::now();

    double local_time = chrono::duration<double>(end - start).count();

    if (rank == 0)
        C.resize(n, vector<double>(n));

    if (rank == 0) {
        int offset = 0;

        for (int p = 0; p < size; ++p) {
            int recv_rows = rows + (p < remainder ? 1 : 0);

            if (p == 0) {
                for (int i = 0; i < recv_rows; ++i)
                    C[i] = localC[i];
            } else {
                MPI_Recv(
                    &C[offset][0],
                    recv_rows * n,
                    MPI_DOUBLE,
                    p,
                    0,
                    MPI_COMM_WORLD,
                    MPI_STATUS_IGNORE
                    );
            }

            offset += recv_rows;
        }

        writeMatrix("data/matrixC.txt", C, n);

        cout << "Matrix size:" << n << "x" << n << endl;
        cout << "Computation time: " << local_time << "s" << endl;
    } else {
        MPI_Send(&localC[0][0],
            local_rows * n,
            MPI_DOUBLE,
            0,
            0,
            MPI_COMM_WORLD);
    }

    MPI_Finalize();
}