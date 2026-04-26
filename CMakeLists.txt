cmake_minimum_required(VERSION 3.18)
project(parallel_programming CUDA CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

enable_language(CUDA)

add_executable(matrix_cuda src/main.cu
        src/main.cu
        src/main.cu)
