TEST_REQUIREMENTS=nose coverage mock

all: install
install:
	pip install -q . --upgrade
doc: install
	pip install -q sphinx sphinx-autobuild sphinx_rtd_theme
	cd docs; $(MAKE) clean; $(MAKE) html
docopen: doc
	open docs/build/html/index.html
docpdf: install
	pip install sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) latexpdf
l5pc_nbconvert: jupyter
	cd examples/l5pc && \
		jupyter nbconvert --to python L5PC.ipynb && \
		sed '/get_ipython/d;/plt\./d;/plot_responses/d;/import matplotlib/d;/neurom/d;/axes/d;/fig/d;/for index/d' L5PC.py >L5PC.tmp && \
		mv L5PC.tmp L5PC.py && \
		python l5pc_validate_neuron_arbor_pm.py --prepare-only --regions somatic --param-values ../../bluepyopt/tests/testdata/l5pc_validate_neuron_arbor/param_values.json && \
		jupyter nbconvert --to python l5pc_validate_neuron_arbor_somatic.ipynb && \
		sed '/get_ipython/d;/plt\./d;/import matplotlib/d;/from IPython.display/d;/multiprocessing/d;s/pool.map/map/g;s/# test_l5pc: insert //g;/# test_l5pc: skip/d' l5pc_validate_neuron_arbor_somatic.py >l5pc_validate_neuron_arbor_somatic.tmp && \
		mv l5pc_validate_neuron_arbor_somatic.tmp l5pc_validate_neuron_arbor_somatic.py
l5pc_nrnivmodl:
	cd examples/l5pc && nrnivmodl mechanisms
l5pc_zip:
	cd examples/l5pc && \
		zip -qr l5_config.zip config/ morphology/ mechanisms/ l5pc_model.py l5pc_evaluator.py checkpoints/checkpoint.pkl	
l5pc_prepare: l5pc_nbconvert l5pc_nrnivmodl
stochkv_prepare: 
	cd examples/stochkv && ls mechanisms && nrnivmodl mechanisms
sc_prepare: jupyter
	cd examples/simplecell && \
		jupyter nbconvert --to python simplecell.ipynb && \
		sed '/get_ipython/d;/plt\./d;/plot_responses/d;/import matplotlib/d' simplecell.py >simplecell.tmp && \
		mv simplecell.tmp simplecell.py && \
		jupyter nbconvert --to python simplecell_arbor.ipynb && \
		sed '/get_ipython/d;/plt\./d;/plot_responses/d;/import matplotlib/d' simplecell_arbor.py >simplecell_arbor.tmp && \
		mv simplecell_arbor.tmp simplecell_arbor.py

meta_prepare: jupyter
	cd examples/metaparameters && \
		jupyter nbconvert --to python metaparameters.ipynb && \
		sed '/get_ipython/d;/plt\./d;/plot_responses/d;/import matplotlib/d' metaparameters.py >metaparameters.tmp && \
		mv metaparameters.tmp metaparameters.py
coverage_unit: unit
	cd bluepyopt/tests; coverage html -d coverage_html; open coverage_html/index.html 
coverage_test: test
	cd bluepyopt/tests; coverage html -d coverage_html; open coverage_html/index.html 
jupyter:
	pip install jupyter
	pip install ipython --upgrade
	pip install papermill
	pip install scipy
install_test_requirements:
	pip install -q $(TEST_REQUIREMENTS) --upgrade
test: clean unit functional
unit: install install_test_requirements
	cd bluepyopt/tests; nosetests -a 'unit' -s -v -x --with-coverage --cover-xml \
		--cover-package bluepyopt;
functional: install install_test_requirements stochkv_prepare l5pc_prepare sc_prepare
	cd bluepyopt/tests; nosetests -a '!unit' -s -v -x --with-coverage --cover-xml \
		--cover-package bluepyopt;
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
	rm -rf bluepyopt/tests/coverage_html
	rm -rf examples/l5pc/L5PC.py
	rm -rf examples/l5pc/l5pc_validate_neuron_arbor_somatic.ipynb
	rm -rf examples/l5pc/l5pc_validate_neuron_arbor_somatic.py
	rm -rf examples/l5pc/x86_64
	rm -rf examples/stochkv/x86_64
	rm -rf .coverage
	rm -rf coverage.xml
	find . -name "*.pyc" -exec rm -rf {} \;
l5pc_start: install
	cd examples/l5pc && \
	@nrnivmodl mechanisms && \
	python ./opt_l5pc.py --start
l5pc_cont: install
	cd examples/l5pc && \
	@nrnivmodl mechanisms && \
	python ./opt_l5pc.py --continue_cp
l5pc_analyse: install
	cd examples/l5pc && \
	@nrnivmodl mechanisms && \
	python ./opt_l5pc.py --analyse
push: clean test
	git push
	git push --tags
check_codecov:
	cat codecov.yml | curl --data-binary @- https://codecov.io/validate
toxbinlinks:
	cd ${TOX_ENVBINDIR}; find $(TOX_NRNBINDIR) -type f -exec ln -sf \{\} . \;
