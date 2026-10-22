#pragma once

/// y = a * x + y on the GPU. Returns false when CUDA reports an error.
bool Saxpy(int n, float a, const float* x, float* y);
