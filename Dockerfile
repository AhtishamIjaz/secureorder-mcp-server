FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory
WORKDIR /app

# Create a non-root user for Hugging Face security (User 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy project files and change ownership
COPY --chown=user:user . .

# Install dependencies using uv
RUN uv sync

# Expose port for Hugging Face
EXPOSE 7860

# Run the MCP server
CMD ["uv", "run", "app.py"]