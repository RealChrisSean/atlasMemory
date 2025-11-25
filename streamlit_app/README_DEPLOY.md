# atlasMemory Streamlit Deployment

## Local Development

```bash
cd streamlit_app
pip install -r requirements.txt

# Create .streamlit/secrets.toml for local testing
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
[tidb]
user = "your_tidb_user"
password = "your_tidb_password"
host = "gateway01.xxx.prod.aws.tidbcloud.com"
port = "4000"
database = "your_db_name"
ca_path = "/etc/ssl/cert.pem"
EOF

streamlit run app.py
```

## Streamlit Cloud Deployment

1. Push this folder to GitHub (or use the main repo)

2. Go to [share.streamlit.io](https://share.streamlit.io)

3. Click "New app" and connect your repo

4. Set:
   - Repository: `your-username/atlasMemoryDRAFT`
   - Branch: `main`
   - Main file path: `streamlit_app/app.py`

5. Click "Advanced settings" → "Secrets" and add:

```toml
[tidb]
user = "your_tidb_user"
password = "your_tidb_password"
host = "gateway01.xxx.prod.aws.tidbcloud.com"
port = "4000"
database = "your_db_name"
ca_path = "/etc/ssl/certs/ca-certificates.crt"
```

6. Deploy!

## Notes

- Each visitor gets a unique `user_id` so demos don't conflict
- The app auto-initializes the database table on first run
- TiDB credentials should be read-only for safety
