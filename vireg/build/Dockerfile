# vireg container image.
#
# Uses Microsoft's official Playwright image (Ubuntu 24.04 "noble") so that
# vireg can run on hosts whose OS is not supported by Playwright (e.g. Ubuntu 26).
# The tag is pinned to the exact Playwright version in package-lock.json so the
# bundled browsers match the installed playwright npm package.

FROM mcr.microsoft.com/playwright:v1.50.1-noble

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY build/entrypoint.sh /usr/local/bin/vireg-entrypoint.sh
RUN chmod +x /usr/local/bin/vireg-entrypoint.sh

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV npm_config_cache=/tmp/npm-cache

ENTRYPOINT ["/usr/local/bin/vireg-entrypoint.sh"]
