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
test: install
	pip install nose coverage --upgrade
	cd examples/l5pc && nrnivmodl mechanisms
	cd bluepyopt/tests; nosetests -s -v -x --with-coverage --cover-xml \
		--cover-package bluepyopt
example: install
	cd examples/simplecell && \
	python ./opt_simplecell.py
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
