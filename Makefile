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

tests: clean
	-docker-compose stop
	-docker-compose rm -f
	docker-compose run --rm test tox -e py27-django18
	docker-compose run --rm test tox -e py27-django110

# target: setup-lo0
# Configures loopback interafce so the Selenium Docker container can access
# Django's LiveServer. Used on macOS. 
setup-lo0:
	sudo ifconfig lo0 alias 192.168.13.37
