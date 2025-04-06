FROM python:3.12
WORKDIR /app

# Install the application dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY ./ ./
EXPOSE 8443

# Setup an app user so the container doesn't run as the root user, also add permission for /app to the new user
RUN useradd app; chmod -R u+rwx .; chown -R app .
USER app

CMD ["streamlit", "run", "./platform-ui.py", "--server.port", "8443"]