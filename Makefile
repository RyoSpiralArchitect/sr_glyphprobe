.PHONY: test smoke plan matrix clean

test:
	PYTHONPATH=src pytest -q
	python -m compileall -q src/glyphprobe

smoke:
	PYTHONPATH=src python -m glyphprobe run -c configs/v1_smoke.yaml

plan:
	PYTHONPATH=src python -m glyphprobe plan -c configs/v1_standard.yaml --num-layers 12

matrix:
	PYTHONPATH=src python -m glyphprobe matrix -x configs/backend_matrix.example.yaml --dry-run

clean:
	rm -rf .pytest_cache build dist runs
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
