# ---------- build stage: install deps into a venv on alpine ----------
FROM python:3.12-alpine AS builder

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# ---------- runtime: alpine, only venv + code ----------
FROM python:3.12-alpine

RUN rm -rf /usr/local/lib/python3.12/idlelib \
    /usr/local/lib/python3.12/lib2to3 \
    /usr/local/lib/python3.12/test \
    /usr/local/lib/python3.12/ensurepip \
    /usr/local/include /tmp/* \
    && apk del --purge -R .locked-deps 2>/dev/null; true

WORKDIR /app

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY . .

USER nobody:nogroup

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]