all: clean

clean:
	rm -rf logs/*
	rm models/*.pyc
	rm modes/*.pyc
	rm *.pyc
	touch logs/shinymud.log