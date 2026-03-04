# dark-governance CLI build system
# Requires: Go 1.22+, golangci-lint (optional, for lint target)

BINARY_NAME := dark-governance
MODULE := github.com/SET-Apps/ai-submodule/src
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
LDFLAGS := -ldflags "-s -w \
	-X $(MODULE)/internal/version.Version=$(VERSION) \
	-X $(MODULE)/internal/version.Commit=$(COMMIT) \
	-X $(MODULE)/internal/version.Date=$(DATE)"

GO := go
GOFLAGS := -trimpath
CONTENT_DIR := internal/embed/_content
GOVERNANCE_DIR := ../governance
DOCS_DIR := ../docs

.PHONY: all build test test-e2e lint vet clean prepare-embed help

## all: Build the binary (default target)
all: build

## build: Compile the dark-governance binary (runs prepare-embed first)
build: prepare-embed
	$(GO) build $(GOFLAGS) $(LDFLAGS) -o bin/$(BINARY_NAME) ./cmd/dark-governance/

## test: Run all tests
test:
	$(GO) test -v -race -count=1 ./...

## test-e2e: Run VHS end-to-end tests (requires VHS + dark-governance on PATH)
test-e2e:
	bash ../tests/e2e/run-tests.sh

## lint: Run golangci-lint
lint:
	golangci-lint run ./...

## vet: Run go vet
vet:
	$(GO) vet ./...

## clean: Remove build artifacts
clean:
	rm -rf bin/
	rm -rf $(CONTENT_DIR)/*
	touch $(CONTENT_DIR)/.gitkeep

## prepare-embed: Copy governance content into _content/ for embedding
##   Copies: policy profiles, schemas, review prompts, personas, commands,
##   workflow templates, language templates, instructions, CLAUDE.md, and curated docs.
##   Excludes: Python engine source, tests, future/ subdirs, __pycache__.
prepare-embed:
	@echo "Preparing embedded governance content..."
	rm -rf $(CONTENT_DIR)/*
	mkdir -p $(CONTENT_DIR)
	@if [ -d "$(GOVERNANCE_DIR)" ]; then \
		echo "  Copying policy profiles..."; \
		mkdir -p $(CONTENT_DIR)/policy; \
		cp $(GOVERNANCE_DIR)/policy/*.yaml $(CONTENT_DIR)/policy/ 2>/dev/null || true; \
		echo "  Copying schemas..."; \
		mkdir -p $(CONTENT_DIR)/schemas; \
		cp $(GOVERNANCE_DIR)/schemas/*.json $(CONTENT_DIR)/schemas/ 2>/dev/null || true; \
		cp $(GOVERNANCE_DIR)/schemas/*.schema.json $(CONTENT_DIR)/schemas/ 2>/dev/null || true; \
		echo "  Copying review prompts..."; \
		mkdir -p $(CONTENT_DIR)/prompts/reviews; \
		cp $(GOVERNANCE_DIR)/prompts/reviews/*.md $(CONTENT_DIR)/prompts/reviews/ 2>/dev/null || true; \
		echo "  Copying personas..."; \
		mkdir -p $(CONTENT_DIR)/personas/agentic; \
		cp $(GOVERNANCE_DIR)/personas/agentic/*.md $(CONTENT_DIR)/personas/agentic/ 2>/dev/null || true; \
		echo "  Copying commands..."; \
		mkdir -p $(CONTENT_DIR)/commands; \
		cp $(GOVERNANCE_DIR)/commands/*.md $(CONTENT_DIR)/commands/ 2>/dev/null || true; \
		echo "  Copying workflow templates..."; \
		mkdir -p $(CONTENT_DIR)/templates/workflows; \
		cp $(GOVERNANCE_DIR)/templates/workflows/*.yml $(CONTENT_DIR)/templates/workflows/ 2>/dev/null || true; \
		echo "  Copying language templates..."; \
		cp -r $(GOVERNANCE_DIR)/templates/languages $(CONTENT_DIR)/templates/languages 2>/dev/null || true; \
		echo "  Copying instructions..."; \
		cp ../instructions.md $(CONTENT_DIR)/instructions.md 2>/dev/null || true; \
		cp ../CLAUDE.md $(CONTENT_DIR)/CLAUDE.md 2>/dev/null || true; \
		echo "  Copying curated docs (~18 high-value topics)..."; \
		mkdir -p $(CONTENT_DIR)/docs/onboarding; \
		cp $(DOCS_DIR)/onboarding/eli5.md $(CONTENT_DIR)/docs/onboarding/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/onboarding/developer-guide.md $(CONTENT_DIR)/docs/onboarding/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/onboarding/project-structure.md $(CONTENT_DIR)/docs/onboarding/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/onboarding/cheat-sheet.md $(CONTENT_DIR)/docs/onboarding/ 2>/dev/null || true; \
		mkdir -p $(CONTENT_DIR)/docs/architecture; \
		cp $(DOCS_DIR)/architecture/governance-model.md $(CONTENT_DIR)/docs/architecture/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/architecture/agent-architecture.md $(CONTENT_DIR)/docs/architecture/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/architecture/context-management.md $(CONTENT_DIR)/docs/architecture/ 2>/dev/null || true; \
		mkdir -p $(CONTENT_DIR)/docs/guides; \
		cp $(DOCS_DIR)/guides/installation.md $(CONTENT_DIR)/docs/guides/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/guides/developer-quickstart.md $(CONTENT_DIR)/docs/guides/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/guides/unified-cli-reference.md $(CONTENT_DIR)/docs/guides/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/guides/project-yaml-configuration.md $(CONTENT_DIR)/docs/guides/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/guides/migration-submodule-to-binary.md $(CONTENT_DIR)/docs/guides/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/guides/updating.md $(CONTENT_DIR)/docs/guides/ 2>/dev/null || true; \
		mkdir -p $(CONTENT_DIR)/docs/configuration; \
		cp $(DOCS_DIR)/configuration/repository-setup.md $(CONTENT_DIR)/docs/configuration/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/configuration/ci-gating.md $(CONTENT_DIR)/docs/configuration/ 2>/dev/null || true; \
		mkdir -p $(CONTENT_DIR)/docs/reference; \
		cp $(DOCS_DIR)/reference/panel-catalog.md $(CONTENT_DIR)/docs/reference/ 2>/dev/null || true; \
		cp $(DOCS_DIR)/reference/policy-comparison.md $(CONTENT_DIR)/docs/reference/ 2>/dev/null || true; \
		mkdir -p $(CONTENT_DIR)/docs/tutorials; \
		cp $(DOCS_DIR)/tutorials/end-to-end-walkthrough.md $(CONTENT_DIR)/docs/tutorials/ 2>/dev/null || true; \
		echo "Governance content prepared in $(CONTENT_DIR)/"; \
		echo "Contents:"; \
		find $(CONTENT_DIR) -type f | wc -l | xargs -I {} echo "  {} files embedded"; \
	else \
		echo "Warning: $(GOVERNANCE_DIR) directory not found. Using placeholder."; \
		touch $(CONTENT_DIR)/.gitkeep; \
	fi

## help: Show this help message
help:
	@echo "Available targets:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
