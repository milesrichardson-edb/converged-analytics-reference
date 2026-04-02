# 1. Use an official lightweight Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements first (to cache dependencies)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY app.py .

# 6. Expose the port the app runs on
EXPOSE 8000

# 7. Command to run the application
# Note: We use --host 0.0.0.0 so the container is accessible from outside
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]