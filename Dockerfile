FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# 1. Set the working directory
WORKDIR /app

# 2. Copy the configuration files FIRST (Efficiency Logic)
COPY pyproject.toml uv.lock ./

# 3. Install dependencies as ROOT (to ensure success)
# --no-install-project tells uv to just get the libraries ready
RUN uv sync --no-install-project --no-dev

# 4. Create the restricted user for Hugging Face security
RUN useradd -m -u 1000 user

# 5. Copy the rest of the application and set ownership
COPY --chown=user:user . .

# 6. Switch to the non-root user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 7. Expose the port
EXPOSE 7860

# 8. Run the app
CMD ["uv", "run", "app.py"]