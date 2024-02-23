#!/bin/bash

set -e

exec bundle exec jekyll serve --drafts --incremental --host 0.0.0.0 --config _config.yml,_config_dev.yml