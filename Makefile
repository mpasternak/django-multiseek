clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -rf test_project/splintershots test_project/node_modules test_project/components
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

install-wheels:
	pip2 install --no-index --find-links=dist -rrequirements_dev.txt
	pip3 install --no-index --find-links=dist -rrequirements_dev.txt

wheels:
	pip wheel -w dist -rrequirements_dev.txt

docker: wheels
	docker-compose build test

# cel: setup-lo0
# Konfiguruje alias IP dla interfejsu lo0 aby kontener Dockera 'selenium'
# miał dostęp do live-serwera uruchamianego na komputerze hosta. Użyteczne
# pod Mac OS X
setup-lo0:
	sudo ifconfig lo0 alias 192.168.13.37

