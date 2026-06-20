.PHONY: bootstrap test

bootstrap:
	python3 -m pip install -r requirements.txt
	npm install --prefix ../dashboard
	terraform -chdir=../d1-terraform init -backend=false
	@echo "Bootstrap complete"

test:
	cd ../d3-ci-pipeline && PYTHONPATH=. python3 -m pytest tests/ -q
	@echo "Tests passed"
