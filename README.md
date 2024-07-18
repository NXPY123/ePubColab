# Collaborative EPUB Reader
This repository provides the backend functionality for a Collaborative epubReader application. Users can create accounts, upload their epubs, share them with others, and collaboratively read, highlight, and annotate the ebooks.

# Table of Contents
- Features
- Prerequisites
- Setup
- Usage

# Features
- ePub Upload: Users can upload their epub files for reading and annotation.
- Sharing: Users can grant other users access to their uploaded epubs.
- Collaborative Reading: Users can read shared epubs concurrently.
- Highlighting and Annotations: Users can highlight text passages and add notes to the epub, visible to all collaborators.

# Setup
1. Clone the repository
```bash
git clone https://github.com/NXPY123/ePubColab
```
2. Move into the directory
```bash
cd ePubColab
```
3. Create a virtual environment and activate it.
4. Create the Docker image and start the containers
```bash
docker-compose build
docker-compose up
```

To setup locust for load testing, run the following command instead:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```


5. Create an `ePubColab.conf` file inside `/opt/homebrew/etc/nginx/servers/`
6. Paste the following inside the `ePubColab.conf` file:
```conf
server {
    listen 80;
    server_name epubColab.com;
    client_max_body_size 20M;



    location /media {
        root /path/to/repository/ePubColab/ePubColab;
        secure_link $arg_md5,$arg_expires;
        secure_link_md5 "$secure_link_expires$uri 4e43521842759a866b0b96d85f7688cac3ff94e63666b4da97a310af21e304af";

        if ($secure_link = "") {
            return 403;
        }

        if ($secure_link = "0") {
            return 410;
        }


    }


    location / {
        proxy_pass http://127.0.0.1:8000; # Forward requests to the Django development server
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
7. Start the nginx server by running the following command inside the directory
```bash
sudo nginx
```
-- --

Locust can be accessed at: `http://localhost:8089/`

# Usage
This backend provides RESTful API endpoints for user management, epub upload/download, sharing, and annotation functionalities.
The endpoints are specified in the Postman Collection exported as `postman.json` in the repo.
