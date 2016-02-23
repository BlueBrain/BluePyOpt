all: install
install:
	pip install -r requirements.txt . --upgrade
doc: install
	pip install sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) html
doc_upload: doc
	cd docs/build/html && \
	touch .nojekyll && \
	git init . && \
	git add . && \
	git commit -m "Updating docs" && \
	git push "git@github.com:BlueBrain/BluePyOpt.git" master:gh-pages --force && \
	rm -rf .git	
docopen: doc
	open docs/build/html/index.html
docpdf: install
	pip install sphinx sphinx-autobuild
	cd docs; $(MAKE) clean; $(MAKE) latexpdf
test: install clean
	pip install jupyter
	pip install nose coverage --upgrade
	cd examples/l5pc && nrnivmodl mechanisms
	cd examples/simplecell && \
		jupyter nbconvert --to python simplecell.ipynb && \
		sed '/get_ipython/d;/plt\./d;/plot_responses/d;/import matplotlib/d' simplecell.py >simplecell.tmp && \
		mv simplecell.tmp simplecell.py
	cd bluepyopt/tests; nosetests -s -v -x --with-coverage --cover-xml \
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
push: clean test doc_upload
	git push
	git push --tags
