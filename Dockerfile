FROM python:3.11-slim

WORKDIR /site


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /site/

RUN sed -i '1s/^\xEF\xBB\xBF//' /site/entrypoint.sh \
    && sed -i 's/\r$//' /site/entrypoint.sh \
    && chmod +x /site/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "/site/entrypoint.sh"]

CMD ["gunicorn", "--config", "gunicorn.conf.py", "--bind", "0.0.0.0:8000", "wsgi:app"]