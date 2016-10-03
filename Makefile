TEST_REQUIREMENTS=nose coverage

all: install
install:
	pip install -q . --upgrade
doc: install
	pip install -q sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) html
docopen: doc
	open docs/build/html/index.html
docpdf: install
	pip install sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) latexpdf
l5pc_nbconvert: jupyter
	cd examples/l5pc && \
		jupyter nbconvert --to python L5PC.ipynb && \
		sed '/get_ipython/d;/plt\./d;/^plot_responses/d;/import matplotlib/d;/neurom/d' L5PC.py >L5PC.tmp && \
		mv L5PC.tmp L5PC.py
l5pc_nrnivmodl:
	cd examples/l5pc && nrnivmodl mechanisms
l5pc_zip:
	cd examples/l5pc && \
		zip -qr l5_config.zip config/ morphology/ mechanisms/ l5pc_model.py l5pc_evaluator.py checkpoints/checkpoint.pkl	
l5pc_prepare: l5pc_zip l5pc_nbconvert l5pc_nrnivmodl
stochkv_prepare: 
	cd examples/stochkv && \
	nrnivmodl mechanisms
sc_prepare: jupyter
	cd examples/simplecell && \
		jupyter nbconvert --to python simplecell.ipynb && \
		sed '/get_ipython/d;/plt\./d;/plot_responses/d;/import matplotlib/d' simplecell.py >simplecell.tmp && \
		mv simplecell.tmp simplecell.py
jupyter:
	pip install -q jupyter
install_test_requirements:
	pip install -q $(TEST_REQUIREMENTS) --upgrade
test: clean unit functional
unit: install install_test_requirements
	cd bluepyopt/tests; nosetests -a 'unit' -s -v -x --with-coverage --cover-xml \
		--cover-package bluepyopt
functional: install install_test_requirements stochkv_prepare l5pc_prepare sc_prepare
	cd bluepyopt/tests; nosetests -a '!unit' -s -v -x --with-coverage --cover-xml \
		--cover-package bluepyopt
pypi: test
	pip install twine --upgrade
	rm -rf dist
	python setup.py sdist bdist
	twine upload dist/*
example: install
	cd examples/simplecell && \
	python ./opt_simplecell.py
clean:
	rm -rf build
	rm -rf docs/build
	rm -rf bluepyopt/tests/.coverage
	rm -rf bluepyopt/tests/coverage.xml
	find . -name "*.pyc" -exec rm -rf {} \;
l5pc_start: install
	cd examples/l5pc && \
	nrnivmodl mechanisms && \
	python ./opt_l5pc.py --start
l5pc_cont: install
	cd examples/l5pc && \
	nrnivmodl mechanisms && \
	python ./opt_l5pc.py --continue_cp
l5pc_analyse: install
	cd examples/l5pc && \
	nrnivmodl mechanisms && \
	python ./opt_l5pc.py --analyse
push: clean test
	git push
	git push --tags
check_codecov:
	cat codecov.yml | curl --data-binary @- https://codecov.io/validate
