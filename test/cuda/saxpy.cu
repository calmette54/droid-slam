#include "test/cuda/saxpy.h"

#include <cuda_runtime.h>

namespace {
  __global__ void SaxpyKernel(int n, float a, const float* x, float* y) {
    const int i = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
    if (i < n) {
      y[i] = a * x[i] + y[i];
    }
  }
}  // namespace

bool Saxpy(int n, float a, const float* x, float* y) {
  float* d_x = nullptr;
  float* d_y = nullptr;
  const size_t bytes = static_cast<size_t>(n) * sizeof(float);
  if (cudaMalloc(&d_x, bytes) != cudaSuccess || cudaMalloc(&d_y, bytes) != cudaSuccess) {
    return false;
  }
  cudaMemcpy(d_x, x, bytes, cudaMemcpyHostToDevice);
  cudaMemcpy(d_y, y, bytes, cudaMemcpyHostToDevice);
  constexpr int kThreads = 256;
  SaxpyKernel<<<(n + kThreads - 1) / kThreads, kThreads>>>(n, a, d_x, d_y);
  const bool ok = cudaGetLastError() == cudaSuccess && cudaDeviceSynchronize() == cudaSuccess;
  cudaMemcpy(y, d_y, bytes, cudaMemcpyDeviceToHost);
  cudaFree(d_x);
  cudaFree(d_y);
  return ok;
}
