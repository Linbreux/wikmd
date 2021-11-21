all: deploy

build:
	podman build -t repo.rcmd.space/wiki-ng:latest .
	podman push repo.rcmd.space/wiki-ng:latest

deploy: build
	install -D -m 644 config/systemd/* /etc/systemd/system
	systemctl daemon-reload
	systemctl enable wiki-ng.service
	systemctl stop wiki-ng.service
	systemctl start wiki-ng.service
