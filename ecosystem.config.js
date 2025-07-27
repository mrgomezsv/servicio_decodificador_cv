module.exports = {
  apps: [{
    name: 'cv-decoder-service',
    script: 'main.py',
    interpreter: './venv/bin/python',
    cwd: '/ruta/completa/a/Servicio_Decodificador_CV',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'development',
      PORT: 8001
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 8001
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    max_restarts: 10,
    min_uptime: '10s',
    restart_delay: 4000
  }]
}; 