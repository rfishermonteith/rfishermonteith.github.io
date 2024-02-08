.PHONY: run

run:
	docker-compose up

clean-and-run: run
	if [ -d _site ]; then rm -Rf _site; fi;
