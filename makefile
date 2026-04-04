all:
	git pull
	sudo podman build -t ascii-clock . 
	sudo podman stop ascii
	sudo podman rm ascii
	sudo podman run -d --network=host --name ascii --restart unless-stopped localhost/ascii-clock:latest