#include <iostream>
#include <vector>
#include <chrono>
#include <fstream>
#include <stdexcept>
#include <iomanip>

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

int main() {
        int n1, n2;

        vector<vector<double>> A = readMatrix("data/matrixA.txt", n1);
        vector<vector<double>> B = readMatrix("data/matrixB.txt", n2);

        if (n1 <= 0 || n2 <= 0) {
            cout << "Invalid number of rows and columns." << endl;
            return 1;
        }

        if (n1 != n2) {
            cout << "Matrices must be the same size" << endl;
            return 1;
        }

        auto start = chrono::high_resolution_clock::now();

        vector<vector<double>> C = multMatrix(A, B, n1);

        auto end = chrono::high_resolution_clock::now();

        std::chrono::duration<double> elapsedTime = end - start;

        writeMatrix("data/matrixC.txt", C, n1);

        cout << "Matrix size: " << n1 << "x" << n1 << endl;
        cout << "Computation time: " << elapsedTime.count() << " seconds" << endl;
        cout << "Result saved to matrixC.txt" << endl;

}

