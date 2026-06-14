# Document Analysis RAG AWS Hybrid Mode

Document Analysis RAG can be deployed as a low-cost AWS demo on one EC2 instance. FastAPI, Streamlit, document parsing, embeddings, vector storage, and retrieval run on the instance. Groq generates the final answer, so retrieved excerpts are sent to Groq.

Use public/demo documents only in AWS hybrid mode.

## Architecture

- EC2 instance runs FastAPI on `127.0.0.1:8000`.
- EC2 instance runs Streamlit on `127.0.0.1:8501`.
- Nginx exposes the app on public HTTP port `80`.
- Nginx routes `/` to Streamlit and `/api/*` to FastAPI.
- Uploads and indexes are stored under `/opt/insight-ai/data`.
- Secrets are stored in `/opt/insight-ai/.env`.

## Free-Tier Notes

AWS free usage depends on your account plan, credits, region, storage, data transfer, and how long the instance runs. For a resume demo, keep the instance small, stop or terminate it when not needed, and set a billing alert before deploying.

Recommended low-cost demo shape:

- One Ubuntu EC2 instance.
- 20-30 GB `gp3` EBS volume.
- HTTP only for a temporary demo, or add HTTPS later with a domain.
- Groq API key for answer generation.

The local embedding model can be memory-heavy. If a tiny free-tier instance runs out of memory while installing dependencies or indexing documents, use a small paid burstable instance for the demo window, then stop it after recording screenshots/video.

## AWS Setup

Launch an Ubuntu EC2 instance and open inbound security group rules:

- SSH `22` from your IP only.
- HTTP `80` from anywhere for the demo.

### Scripted Setup

SSH into the instance, then install system packages:

```bash
sudo apt update
sudo apt install -y git
sudo mkdir -p /opt/insight-ai
sudo chown -R ubuntu:ubuntu /opt/insight-ai
git clone https://github.com/faisalcn24/insight-ai-2.git /opt/insight-ai/app
cd /opt/insight-ai/app
bash deploy/setup_ec2.sh
```

Then edit `/opt/insight-ai/.env`, set `GROQ_API_KEY`, and restart services:

```bash
nano /opt/insight-ai/.env
sudo systemctl restart insight-api insight-ui
```

### Manual Setup

Use this path if you want to run each step yourself or debug a failed scripted setup.

Install system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv nginx git
sudo mkdir -p /opt/insight-ai/data /opt/insight-ai/app
sudo chown -R ubuntu:ubuntu /opt/insight-ai
```

Clone the project:

```bash
git clone https://github.com/faisalcn24/insight-ai-2.git /opt/insight-ai/app
cd /opt/insight-ai/app
```

Create the virtual environment and install dependencies:

```bash
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

Create the production environment file:

```bash
cp .env.example /opt/insight-ai/.env
nano /opt/insight-ai/.env
```

Use these values on EC2:

```env
GROQ_API_KEY=replace-with-your-groq-key
GROQ_MODEL=llama-3.1-8b-instant
INSIGHT_LLM_PROVIDER=groq
INSIGHT_API_BASE_URL=http://127.0.0.1:8000
INSIGHT_STORAGE_DIR=/opt/insight-ai/data
```

Install the systemd and Nginx templates:

```bash
sudo cp deploy/insight-api.service /etc/systemd/system/
sudo cp deploy/insight-ui.service /etc/systemd/system/
sudo cp deploy/nginx-insight-ai.conf /etc/nginx/sites-available/insight-ai
sudo ln -sf /etc/nginx/sites-available/insight-ai /etc/nginx/sites-enabled/insight-ai
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now insight-api insight-ui nginx
```

## Smoke Test

Check the backend directly:

```bash
curl http://127.0.0.1:8000/health
```

Check the public Nginx route from the instance:

```bash
curl http://127.0.0.1/api/health
```

Open the EC2 public IPv4 address in a browser:

```text
http://<ec2-public-ip>
```

Upload a small public PDF, DOCX, or XLSX file, create a searchable collection, and ask a question.

## Operations

View service status:

```bash
sudo systemctl status insight-api
sudo systemctl status insight-ui
sudo systemctl status nginx
```

View logs:

```bash
sudo journalctl -u insight-api -f
sudo journalctl -u insight-ui -f
```

Restart after code or environment changes:

```bash
sudo systemctl restart insight-api insight-ui
```

Update the deployed app:

```bash
cd /opt/insight-ai/app
bash deploy/update_app.sh
```

FastAPI endpoints:

- `GET /health`
- `GET /indexes`
- `POST /indexes` with multipart `files` and optional `index_id`
- `DELETE /indexes/{index_id}`
- `POST /chat` with `{"index_id": "...", "message": "..."}`
- `POST /retrieve` with `{"index_id": "...", "query": "...", "top_k": 5}`

AWS deployment templates are in `deploy/`.
