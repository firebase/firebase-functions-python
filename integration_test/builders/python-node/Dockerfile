# Use a combined base image with Python 3.11 and Node 18
FROM python:3.11

# Install Node.js 18 using the Nodesource repository
RUN apt-get update && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*