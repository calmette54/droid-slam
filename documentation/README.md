# API documentation

Reference documentation for the `greeter` library and the `hello-world`
command-line tool. It is generated with [Doxygen](https://www.doxygen.nl/) and
the [Doxygen Awesome](https://github.com/jothepro/doxygen-awesome-css) theme:

```bash
bazelisk build //documentation:docs   # output: bazel-bin/documentation/html
```

Start with greeter::Greeter, or see `standalone/main.cpp` for a usage example.

## Writing documentation

The theme supports the following in Markdown pages and comments.

You can add equations:

$$
\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}
$$

Code snippets:

```cpp
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
```

And even mermaid diagrams:

<pre class="mermaid">
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
</pre>
