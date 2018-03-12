clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -rf test_project/static test_project/bower_components .cache .pytest_cache
	rm -fr .eggs/
	rm -rf test_project/splintershots test_project/node_modules test_project/components > /dev/null || true
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

release: clean ## package and upload a release
	python setup.py sdist upload
	python setup.py bdist_wheel upload

assets:
	cd test_project && yarn
	cd test_project && python manage.py collectstatic --noinput

tests: assets
	pip install detox
	detox


# target: setup-lo0
# Configures loopback interafce so the Selenium Docker container can access
# Django's LiveServer. Used on macOS. 
setup-lo0:
	sudo ifconfig lo0 alias 192.168.13.37

install-yarn-packages-via-docker:
	docker run --rm -v `pwd`:/usr/src/app -it node:alpine /bin/sh -c "cd /usr/src/app/test_project && yarn"

tests-via-docker: clean install-yarn-packages-via-docker
	docker-compose up -d
	docker-compose exec test /bin/bash -c "cd /usr/src/app && pip install tox && tox"

update-messages:
	cd multiseek && django-admin.py makemessages -d django -d djangojs -a
