all:
	git pull
	sudo podman build -t ascii-clock . 
	sudo podman stop ascii
	sudo podman rm ascii
	sudo podman run -d --network=host --name ascii --restart unless-stopped localhost/ascii-clock:latest

clean:
	sudo podman stop ascii
	sudo podman rm ascii
	sudo podman rmi ascii-clock:latest
	sudo podman rmi python:slim