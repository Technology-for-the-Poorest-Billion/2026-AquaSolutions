.PHONY: orgunits metadata test

orgunits:
	PYTHONPATH=. python -m metadata.generate_org_units
	PYTHONPATH=. python -m metadata.import_metadata metadata/org_units.json

metadata:
	PYTHONPATH=. python -m metadata.generate_org_units
	PYTHONPATH=. python -m metadata.import_metadata metadata/org_units.json
	PYTHONPATH=. python -m metadata.import_metadata metadata/program_illness.json
	PYTHONPATH=. python -m metadata.import_metadata metadata/program_water.json
	PYTHONPATH=. python -m metadata.import_metadata metadata/users_roles.json

test:
	python -m pytest -v
