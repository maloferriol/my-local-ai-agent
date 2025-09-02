# Misc

## 1. Creating a Virtual Environment (Recommended)

A virtual environment isolates your project's dependencies.

```bash
python -m venv .venv          # Create the environment
source .venv/bin/activate    # Activate (Linux/macOS)
```

## 2. Push to GitHub

```bash
git add .                     # Stage changes
git commit -m "<commit message>"  # Commit with a message
git push -u origin main       # Push to remote
```

## 3. Run Arize Phoenix Docker

```bash
docker run -p 6006:6006 -p 4319:4317 -i -t arizephoenix/phoenix:latest
```

## 4. Run All Tests

```bash
python -m