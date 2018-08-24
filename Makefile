
.PHONY: clean

clean:
	rm -rf venv dist build dplaapi.egg-info .pytest_cache .coverage \
	    coverage.xml htmlcov *.zip
	find dplaapi tests -type d -name __pycache__ -exec rm -rf {} \; \
		2>/dev/null || true
	test "x${VIRTUAL_ENV}" != "x" && echo "Type 'deactivate' to exit venv." \
		|| true

zip:
	zip dplaapi.zip -x '.git/*' -r * .[^.]*
