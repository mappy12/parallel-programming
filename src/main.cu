#include <iostream>
#include <vector>
#include <fstream>
#include <chrono>
#include <cuda_runtime.h>
#include <cmath>

using namespace std;

__global__ void matrixMulKernel(const double *A, const double *B, double *C, int n) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;

    if (row < n && col < n) {
        double sum = 0.0;
        for (int k = 0; k < n; k++) {
            sum += A[row * n + k] * B[k * n + col];
        }
        C[row * n + col] = sum;
    }
}

bool readMatrixFlat(const string& filename, vector<double>& matrix, int& n) {
    ifstream file(filename);
    if (!file.is_open()) return false;
    file >> n;
    matrix.resize(n * n);
    for (int i = 0; i < n * n; ++i) {
        file >> matrix[i];
    }
    return true;
}

void writeMatrixFlat(const string& filename, const vector<double>& matrix, int n) {
    ofstream file(filename);
    if (!file.is_open()) {
        cerr << "Error opening file for writing" << endl;
        return;
    }
    file << n << endl;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            file << matrix[i * n + j] << " ";
        }
        file << endl;
    }
}

#define cudaCheckError(ans) { gpuAssert((ans), __FILE__, __LINE__); }
inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort=true) {
    if (code != cudaSuccess) {
        fprintf(stderr, "GPUassert: %s %s %d\n", cudaGetErrorString(code), file, line);
        if (abort) exit(code);
    }
}

int main(int argc, char** argv) {
    int blockSizeX = 16;
    int blockSizeY = 16;

    if (argc > 1) {
        blockSizeX = atoi(argv[1]);
        blockSizeY = blockSizeX;
    }

    int n = 0;
    vector<double> A_host, B_host, C_host;

    if (!readMatrixFlat("data/matrixA.txt", A_host, n)) {
        cerr << "Error reading matrixA.txt" << endl;
        return 1;
    }

    ifstream fb("data/matrixB.txt");
    if (!fb.is_open()) {
        cerr << "Error reading matrixB.txt" << endl;
        return 1;
    }
    int n_tmp;
    fb >> n_tmp;
    B_host.resize(n * n);
    for (int i = 0; i < n * n; ++i) fb >> B_host[i];
    fb.close();

    cout << "Matrix size: " << n << "x" << n << endl;
    cout << "Block size: " << blockSizeX << "x" << blockSizeY << endl;

    double *A_device, *B_device, *C_device;
    size_t memSize = n * n * sizeof(double);

    cudaCheckError(cudaMalloc((void**)&A_device, memSize));
    cudaCheckError(cudaMalloc((void**)&B_device, memSize));
    cudaCheckError(cudaMalloc((void**)&C_device, memSize));

    cudaDeviceSynchronize();
    auto start = chrono::high_resolution_clock::now();

    cudaCheckError(cudaMemcpy(A_device, A_host.data(), memSize, cudaMemcpyHostToDevice));
    cudaCheckError(cudaMemcpy(B_device, B_host.data(), memSize, cudaMemcpyHostToDevice));

    dim3 blockDim(blockSizeX, blockSizeY);
    dim3 gridDim((n + blockSizeX - 1) / blockSizeX,
                 (n + blockSizeY - 1) / blockSizeY);

    matrixMulKernel<<<gridDim, blockDim>>>(A_device, B_device, C_device, n);
    cudaCheckError(cudaGetLastError());

    cudaCheckError(cudaDeviceSynchronize());

    C_host.resize(n * n);
    cudaCheckError(cudaMemcpy(C_host.data(), C_device, memSize, cudaMemcpyDeviceToHost));

    auto end = chrono::high_resolution_clock::now();
    double elapsed = chrono::duration<double>(end - start).count();

    cudaCheckError(cudaFree(A_device));
    cudaCheckError(cudaFree(B_device));
    cudaCheckError(cudaFree(C_device));

    cout << "Total time (Copy + Compute): " << elapsed << " seconds" << endl;

    long long operations = (long long)n * n * n;
    cout << "Task volume (N^3): " << operations << " operations" << endl;

    writeMatrixFlat("data/matrixC.txt", C_host, n);
    cout << "Result saved to data/matrixC.txt" << endl;

    double gflops = (double)operations / (elapsed * 1e9);
    cout << "Performance: " << gflops << " GFLOPS" << endl;

    return 0;
}