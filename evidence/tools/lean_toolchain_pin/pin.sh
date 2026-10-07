set -u
U=https://releases.lean-lang.org/lean4/v4.34.1/lean-4.34.1-linux.tar.zst
curl -fsSL -o lean.tar.zst "$U"; echo "download rc=$?"
sha256sum lean.tar.zst; ls -l lean.tar.zst
curl -fsSL -m 30 https://api.github.com/repos/leanprover/lean4/releases/tags/v4.34.1 > gh_release.json; echo "gh api rc=$?"
python3 -I -c "
import json
d=json.load(open(\"gh_release.json\"))
print(d.get(\"tag_name\"),d.get(\"message\"))
for a in d.get(\"assets\",[]):
    if \"linux\" in a[\"name\"] and \"zst\" in a[\"name\"]: print(a[\"name\"],a.get(\"digest\"),a[\"size\"])
"
