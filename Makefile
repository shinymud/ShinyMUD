all: clean

clean:
	rm -rf src/shinymud/logs/*
	rm src/shinymud/models/*.pyc
	rm src/shinymud/modes/*.pyc
	rm src/shinymud/*.pyc
	touch src/shinymud/logs/shinymud.log
	python scripts/db_create