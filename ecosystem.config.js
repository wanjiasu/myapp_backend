module.exports = {
  apps: [
    {
      name: "betaione_backend",
      script: "env/bin/python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    }
  ]
};