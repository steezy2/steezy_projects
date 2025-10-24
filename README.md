# steezy_projects

Collection of small, fun side projects authored by Arnaud Filliat.

This repository is a personal playground containing a variety of sample apps, utilities, experiments, and learning projects across Python, Go, and other languages. Most projects are self-contained and intended as informal demos or learning notes rather than production-ready software.

## Author

- Arnaud Filliat

## High-level contents

- `finance_python/` — Budgeting and finance-related Python scripts and example CSV data. Contains utilities for parsing CSV statements, generating pie charts, and simple budget tracking. See `finance_python/reqs.txt` for Python dependencies.
- `picto3d/` — Go projects and experiments related to geometry and small 3D/pictograph utilities. Contains `main.go`, tests, and supporting libraries.
- `python-mini-projects/` — A large collection of small Python projects and one-off scripts. Each subproject may include its own README or requirements file.
- `sat_propagation/` — Satellite propagation related code and experiments with its own `requirements.txt` and `src/` folder.

## How to explore

- Look at the top-level folders above and open the contained README or `reqs.txt` files where present.
- For Python projects, create a virtual environment and install dependencies listed in the relevant `reqs.txt` or `requirements*.txt` files.

Example (on Windows using bash):

```bash
# create and activate venv
python -m venv .venv
source .venv/Scripts/activate
# install dependencies if the project has a requirements file
pip install -r finance_python/reqs.txt
```

## Notes

- These projects are primarily educational and experimental. They may contain partial code, old samples, or quick scripts used during exploration. Use at your own discretion.
- If you plan to reuse or extend anything here, consider opening an issue or copying the relevant folder into a new repository and adding tests and proper packaging.

## License

Unless otherwise stated in a subproject, assume code here is free to read and experiment with; if you need a specific license, please ask or add one in a fork.

---

If you want more detail about any specific subfolder, tell me which one and I can expand the README with run instructions, notable files, and quick-start examples for that folder.

