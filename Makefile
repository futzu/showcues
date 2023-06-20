PY3 = python3

default: upload

clean:
	rm -f dist/*
	rm -rf build/*

pkg: clean
	$(PY3) setup.py sdist bdist_wheel

upload: clean pkg	
	twine upload dist/*


