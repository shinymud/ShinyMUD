all: clean

clean:
	rm -rf logs/*
	rm models/*.pyc
	rm *.pyc
	touch logs/shinymud.log