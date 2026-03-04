FROM node:18-alpine

WORKDIR /app

# Install Python for policy engine and naming CLI
RUN apk add --no-cache python3 py3-pip

COPY package*.json ./
RUN npm ci --omit=dev

COPY dist/ ./dist/

# The governance directory must be mounted or copied at build time
# Example: docker build --build-arg GOVERNANCE_SRC=../governance .
# Or mount at runtime: docker run -v /path/to/repo:/app/governance ...
ARG GOVERNANCE_SRC=governance
COPY ${GOVERNANCE_SRC}/ ./governance/

# Configurable governance root — override at runtime with:
#   docker run -e GOVERNANCE_ROOT=/custom/path ...
ENV GOVERNANCE_ROOT=/app

ENTRYPOINT ["sh", "-c", "node dist/index.js --governance-root ${GOVERNANCE_ROOT}"]
