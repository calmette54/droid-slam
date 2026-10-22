#include <vector>

#include "test/cuda/saxpy.h"

int main() {
  constexpr int kN = 1 << 16;
  std::vector<float> x(kN, 1.0F);
  std::vector<float> y(kN, 2.0F);
  if (!Saxpy(kN, 3.0F, x.data(), y.data())) {
    return 1;
  }
  for (const float v : y) {
    if (v != 5.0F) {
      return 1;
    }
  }
  return 0;
}
