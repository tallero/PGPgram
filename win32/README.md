# Build as MSYS2/MinGW package

You probably need to install [`tdlib`](https://gitlab.com/tallero/tdlib-mingw) first.

Then just give `makepkg`, install dependencies with `pacman -S <dependency>` and after build install with `pacman -U <pgpgram_pkg_filename>`.
