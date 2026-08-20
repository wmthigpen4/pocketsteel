# Reproducible Python Environments

The `.in` files are the reviewed direct dependencies. The matching `.lock`
files are compiled for Python 3.12 with exact transitive versions and hashes.

Regenerate all locks with the pinned compiler:

```bash
python -m pip install pip-tools==7.5.3
for target in runtime rag training test deployment chord-reader; do
  python -m piptools compile \
    --generate-hashes \
    --strip-extras \
    --allow-unsafe \
    --resolver=backtracking \
    --output-file "requirements/${target}.lock" \
    "requirements/${target}.in"
done
```

Install one environment, then install the local project without resolving a
second dependency graph:

```bash
python -m pip install -r requirements/test.lock
python -m pip install --no-deps -e .
```

Do not hand-edit compiled lock files. Review changes to the `.in` files first,
then regenerate and audit the locks.
