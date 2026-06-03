.PHONY: orgunits test

orgunits:
	PYTHONPATH=. python -m metadata.generate_org_units
	PYTHONPATH=. python -m metadata.import_metadata metadata/org_units.json

test:
	PYTHONPATH=. pytest -v
