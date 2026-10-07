set -u
mkdir -p lean-x && cd lean-x && export PATH=/home/volmax-studio/volmax-projects/iot2/PORTFOLIO/p10-tools/elan/bin:$PATH
(zstd -dc ../lean.tar.zst 2>/dev/null || unzstd -c ../lean.tar.zst) | tar x 2>&1 | tail -2
ls; D=$(ls -d */ | head -1)
(cd "$D" && find . -type f | LC_ALL=C sort | xargs sha256sum) | sha256sum | tee ../tree_from_verified_tarball.txt
T=/home/volmax-studio/volmax-projects/iot2/PORTFOLIO/p10-tools/elan/toolchains/leanprover--lean4---v4.34.1
(cd "$T" && find . -type f | LC_ALL=C sort | xargs sha256sum) | sha256sum | tee ../tree_from_elan_install.txt
