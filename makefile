all:
	git pull
	sudo podman build -t ascii-clock . 
	sudo podman stop ascii
	sudo podman rm ascii
	sudo podman run -d --name ascii -p 8000:8000 --restart unless-stopped localhost/ascii-clock:latest